import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.candidate_merge import (
    REGRESSION_TEST_COMMANDS, TARGETED_TEST_COMMANDS, create_merge_workspace,
)
from src.repair.merge_validator import validate_merge

FIXTURE = ROOT / "fixtures" / "repair" / "fake_approved_apply_workspace"


def _validate():
    return validate_merge(FIXTURE)


def test_merge_workspace_created():
    v = _validate()
    assert v.valid, v.errors
    with tempfile.TemporaryDirectory() as d:
        m = create_merge_workspace(FIXTURE, v, merge_id="t", base_dir=d, reviewer=v.reviewer)
        ws = Path(m.workspace_dir)
        assert ws.exists()
        for f in ("merge_manifest.json", "merge_report.md", "rollback_plan.md",
                  "promotion_review_package.md", "test_results.json", "README.md"):
            assert (ws / f).exists(), f


def test_merged_changes_created():
    v = _validate()
    with tempfile.TemporaryDirectory() as d:
        m = create_merge_workspace(FIXTURE, v, merge_id="t", base_dir=d, reviewer=v.reviewer)
        merged = Path(m.workspace_dir) / "merged_changes"
        assert merged.exists()
        files = [p for p in merged.rglob("*") if p.is_file()]
        # mirrors the apply workspace's proposed_changes
        src = [p for p in (FIXTURE / "proposed_changes").rglob("*") if p.is_file()]
        assert len(files) == len(src)
        assert len(files) > 0


def test_repo_target_files_not_modified():
    v = _validate()
    # targets referenced by the apply manifest must not be written in the live repo
    targets = [a.get("target", "") for a in (v.manifest.get("actions") or [])]
    before = {t: (ROOT / t).exists() for t in targets if t}
    with tempfile.TemporaryDirectory() as d:
        m = create_merge_workspace(FIXTURE, v, merge_id="t", base_dir=d, reviewer=v.reviewer)
        assert Path(m.workspace_dir).is_relative_to(Path(d))
    after = {t: (ROOT / t).exists() for t in targets if t}
    assert before == after
    assert m.stable_modified is False


def test_rollback_plan_exists_and_describes_reversal():
    v = _validate()
    with tempfile.TemporaryDirectory() as d:
        m = create_merge_workspace(FIXTURE, v, merge_id="t", base_dir=d, reviewer=v.reviewer)
        rb = (Path(m.workspace_dir) / "rollback_plan.md").read_text(encoding="utf-8").lower()
        assert "rollback" in rb
        assert "delete the merge workspace" in rb
        assert m.rollback_available is True


def test_promotion_review_package_exists():
    v = _validate()
    with tempfile.TemporaryDirectory() as d:
        m = create_merge_workspace(FIXTURE, v, merge_id="t", base_dir=d, reviewer=v.reviewer)
        pkg = (Path(m.workspace_dir) / "promotion_review_package.md").read_text(encoding="utf-8").lower()
        assert "promotion review package" in pkg
        assert "human review required" in pkg


def test_report_says_not_promoted():
    v = _validate()
    with tempfile.TemporaryDirectory() as d:
        m = create_merge_workspace(FIXTURE, v, merge_id="t", base_dir=d, reviewer=v.reviewer)
        report = (Path(m.workspace_dir) / "merge_report.md").read_text(encoding="utf-8").lower()
        assert "not promoted" in report
        assert "stable untouched" in report
        assert m.promoted is False
        manifest = json.loads((Path(m.workspace_dir) / "merge_manifest.json").read_text(encoding="utf-8"))
        assert manifest["merged_to_candidate_workspace"] is True
        assert manifest["targeted_tests"] == list(TARGETED_TEST_COMMANDS)
        assert manifest["regression_tests"] == list(REGRESSION_TEST_COMMANDS)


def test_redaction_applied():
    from src.llm.redaction import redact_text
    v = _validate()
    SECRET = "sk-" + "v" * 40
    with tempfile.TemporaryDirectory() as d:
        # inject a secret into the manifest reviewer path indirectly via reviewer
        m = create_merge_workspace(FIXTURE, v, merge_id="t", base_dir=d,
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
