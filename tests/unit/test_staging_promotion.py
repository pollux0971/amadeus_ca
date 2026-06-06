import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.staging_promotion import (
    REGRESSION_TEST_COMMANDS, TARGETED_TEST_COMMANDS, create_staging_workspace,
)
from src.repair.staging_validator import validate_staging

FIXTURE = ROOT / "fixtures" / "repair" / "fake_approved_merge_workspace"


def _validate():
    return validate_staging(FIXTURE)


def test_staging_workspace_created():
    v = _validate()
    assert v.valid, v.errors
    with tempfile.TemporaryDirectory() as d:
        m = create_staging_workspace(FIXTURE, v, staging_id="t", base_dir=d, reviewer=v.reviewer)
        ws = Path(m.workspace_dir)
        assert ws.exists()
        for f in ("staging_manifest.json", "staging_report.md", "rollback_verification.md",
                  "regression_results.json", "stable_promotion_checklist.md", "README.md"):
            assert (ws / f).exists(), f


def test_staged_changes_created():
    v = _validate()
    with tempfile.TemporaryDirectory() as d:
        m = create_staging_workspace(FIXTURE, v, staging_id="t", base_dir=d, reviewer=v.reviewer)
        staged = Path(m.workspace_dir) / "staged_changes"
        assert staged.exists()
        files = [p for p in staged.rglob("*") if p.is_file()]
        src = [p for p in (FIXTURE / "merged_changes").rglob("*") if p.is_file()]
        assert len(files) == len(src)
        assert len(files) > 0


def test_repo_target_files_not_modified():
    v = _validate()
    targets = [a.get("target", "") for a in (v.manifest.get("actions") or [])]
    before = {t: (ROOT / t).exists() for t in targets if t}
    with tempfile.TemporaryDirectory() as d:
        m = create_staging_workspace(FIXTURE, v, staging_id="t", base_dir=d, reviewer=v.reviewer)
        assert Path(m.workspace_dir).is_relative_to(Path(d))
    after = {t: (ROOT / t).exists() for t in targets if t}
    assert before == after
    assert m.stable_modified is False
    assert m.active_candidate_modified is False


def test_rollback_verification_exists():
    v = _validate()
    with tempfile.TemporaryDirectory() as d:
        m = create_staging_workspace(FIXTURE, v, staging_id="t", base_dir=d, reviewer=v.reviewer)
        rb = (Path(m.workspace_dir) / "rollback_verification.md").read_text(encoding="utf-8").lower()
        assert "rollback verification" in rb
        assert "delete the staging workspace" in rb
        assert m.rollback_verified is True


def test_stable_promotion_checklist_exists():
    v = _validate()
    with tempfile.TemporaryDirectory() as d:
        m = create_staging_workspace(FIXTURE, v, staging_id="t", base_dir=d, reviewer=v.reviewer)
        pkg = (Path(m.workspace_dir) / "stable_promotion_checklist.md").read_text(encoding="utf-8").lower()
        assert "stable promotion checklist" in pkg
        assert "promotion policy still required" in pkg or "promotion_policy.md" in pkg


def test_report_says_not_stable_promoted():
    v = _validate()
    with tempfile.TemporaryDirectory() as d:
        m = create_staging_workspace(FIXTURE, v, staging_id="t", base_dir=d, reviewer=v.reviewer)
        report = (Path(m.workspace_dir) / "staging_report.md").read_text(encoding="utf-8").lower()
        assert "not stable promoted" in report
        assert "stable untouched" in report
        assert m.stable_promoted is False
        manifest = json.loads((Path(m.workspace_dir) / "staging_manifest.json").read_text(encoding="utf-8"))
        assert manifest["staged"] is True
        assert manifest["targeted_tests"] == list(TARGETED_TEST_COMMANDS)
        assert manifest["regression_tests"] == list(REGRESSION_TEST_COMMANDS)


def test_redaction_applied():
    from src.llm.redaction import redact_text
    v = _validate()
    SECRET = "sk-" + "y" * 40
    with tempfile.TemporaryDirectory() as d:
        m = create_staging_workspace(FIXTURE, v, staging_id="t", base_dir=d,
                                     reviewer=f"rev {SECRET}")
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
