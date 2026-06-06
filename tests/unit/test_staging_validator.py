import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.staging_validator import (
    STAGING_APPROVAL_MARKER, parse_staging_approval, validate_staging,
)

FIXTURE = ROOT / "fixtures" / "repair" / "fake_approved_merge_workspace"
SECRET = "sk-" + "x" * 40


def _copy_fixture(tmp: Path) -> Path:
    dst = tmp / "mw"
    shutil.copytree(FIXTURE, dst)
    return dst


def _set_manifest(ws: Path, **changes):
    mf = ws / "merge_manifest.json"
    data = json.loads(mf.read_text(encoding="utf-8"))
    data.update(changes)
    mf.write_text(json.dumps(data), encoding="utf-8")


def test_valid_approved_merge_workspace_pass():
    assert validate_staging(FIXTURE).valid


def test_missing_approval_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        (ws / "staging_approval_checklist.md").write_text("no marker", encoding="utf-8")
        r = validate_staging(ws)
        assert not r.valid
        assert any("staging_approval_marker_missing" in e for e in r.errors)


def test_empty_reviewer_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        (ws / "staging_approval_checklist.md").write_text(
            f"{STAGING_APPROVAL_MARKER}: true\nReviewer: TBD\n", encoding="utf-8")
        r = validate_staging(ws)
        assert not r.valid
        assert any("reviewer_empty" in e for e in r.errors)


def test_stable_modified_true_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        _set_manifest(ws, stable_modified=True)
        r = validate_staging(ws)
        assert not r.valid
        assert any("stable_modified" in e for e in r.errors)


def test_promoted_true_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        _set_manifest(ws, promoted=True)
        r = validate_staging(ws)
        assert not r.valid
        assert any("promoted" in e for e in r.errors)


def test_missing_rollback_plan_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        (ws / "rollback_plan.md").unlink()
        r = validate_staging(ws)
        assert not r.valid
        assert any("rollback_plan" in e for e in r.errors)


def test_empty_rollback_plan_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        (ws / "rollback_plan.md").write_text("   \n", encoding="utf-8")
        r = validate_staging(ws)
        assert not r.valid


def test_stable_target_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        _set_manifest(ws, actions=[{"id": "a", "action_type": "update_candidate",
                                    "target": "skills/inspect_project/"}])
        assert not validate_staging(ws).valid


def test_safety_gate_target_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        _set_manifest(ws, actions=[{"id": "a", "action_type": "update_docs",
                                    "target": "src/agents/safety_gate/x.py"}])
        assert not validate_staging(ws).valid


def test_promotion_policy_target_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        _set_manifest(ws, actions=[{"id": "a", "action_type": "update_docs",
                                    "target": "specs/harness/promotion_policy.md"}])
        assert not validate_staging(ws).valid


def test_raw_shell_action_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        _set_manifest(ws, actions=[{"id": "a", "action_type": "raw_shell",
                                    "target": "harnesses/candidates/c/"}])
        assert not validate_staging(ws).valid


def test_secret_looking_staged_change_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        leak = ws / "merged_changes" / "leak.md"
        leak.write_text(f"token {SECRET}", encoding="utf-8")
        r = validate_staging(ws)
        assert not r.valid
        assert any("secret-looking" in e for e in r.errors)
        assert all(SECRET not in e for e in r.errors)


def test_missing_structure_rejected():
    with tempfile.TemporaryDirectory() as d:
        ws = _copy_fixture(Path(d))
        (ws / "merge_manifest.json").unlink()
        assert not validate_staging(ws).valid


def test_parse_staging_approval():
    a = parse_staging_approval(f"{STAGING_APPROVAL_MARKER}: true\nReviewer: jane\n")
    assert a.approved and a.reviewer == "jane"
    assert not parse_staging_approval("Reviewer: jane").approved


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
