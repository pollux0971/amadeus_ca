import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.apply_validator import parse_approval, validate_for_apply
from src.repair.patch_application import (
    ALLOWLISTED_TEST_COMMANDS, apply_proposal, load_proposal_workspace,
)

FIXTURE_WS = ROOT / "fixtures" / "repair" / "fake_approved_proposal_workspace"


def _load_and_validate():
    proposal, analysis, approval_text = load_proposal_workspace(FIXTURE_WS)
    approval = parse_approval(approval_text)
    validation = validate_for_apply(proposal, approval)
    return proposal, approval, validation


def test_apply_workspace_created():
    proposal, approval, validation = _load_and_validate()
    assert validation.valid, validation.errors
    with tempfile.TemporaryDirectory() as d:
        m = apply_proposal(proposal, approval, validation, apply_id="t", base_dir=d)
        ws = Path(m.workspace_dir)
        assert ws.exists()
        for f in ("apply_manifest.json", "apply_report.md", "test_results.json", "README.md"):
            assert (ws / f).exists(), f


def test_proposed_changes_created():
    proposal, approval, validation = _load_and_validate()
    with tempfile.TemporaryDirectory() as d:
        m = apply_proposal(proposal, approval, validation, apply_id="t", base_dir=d)
        proposed = Path(m.workspace_dir) / "proposed_changes"
        assert proposed.exists()
        files = [p for p in proposed.rglob("*") if p.is_file()]
        # one proposed file per non-noop action
        assert len(files) == sum(1 for a in proposal.actions if a.action_type != "noop")


def test_target_repo_files_not_modified():
    # the materialized files live ONLY under the apply workspace; the intended
    # targets in the live repo are never written.
    proposal, approval, validation = _load_and_validate()
    targets = [a.target for a in proposal.actions]
    before = {t: (ROOT / t).exists() for t in targets}
    with tempfile.TemporaryDirectory() as d:
        m = apply_proposal(proposal, approval, validation, apply_id="t", base_dir=d)
        assert Path(m.workspace_dir).is_relative_to(Path(d))
    after = {t: (ROOT / t).exists() for t in targets}
    assert before == after  # no live target created/modified
    assert m.stable_modified is False


def test_report_says_not_promoted():
    proposal, approval, validation = _load_and_validate()
    with tempfile.TemporaryDirectory() as d:
        m = apply_proposal(proposal, approval, validation, apply_id="t", base_dir=d)
        report = (Path(m.workspace_dir) / "apply_report.md").read_text(encoding="utf-8").lower()
        assert "not promoted" in report
        assert "stable untouched" in report
        assert m.promoted is False
        # manifest records the FIXED allowlist
        manifest = json.loads((Path(m.workspace_dir) / "apply_manifest.json").read_text(encoding="utf-8"))
        assert manifest["test_commands"] == list(ALLOWLISTED_TEST_COMMANDS)


def test_redaction_applied():
    from src.llm.redaction import redact_text
    proposal, approval, validation = _load_and_validate()
    # inject a secret into the proposal rationale; it must not survive into artifacts
    SECRET = "sk-" + "r" * 40
    proposal.rationale = f"do not leak {SECRET}"
    with tempfile.TemporaryDirectory() as d:
        m = apply_proposal(proposal, approval, validation, apply_id="t", base_dir=d)
        for f in Path(m.workspace_dir).rglob("*"):
            if f.is_file():
                text = f.read_text(encoding="utf-8")
                assert SECRET not in text
                assert redact_text(text) == text


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
