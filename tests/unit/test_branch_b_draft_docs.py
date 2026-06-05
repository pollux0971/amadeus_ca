import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DRAFT_DIR = ROOT / "docs" / "branch_b_playwright_gate_passed_draft"

_spec = importlib.util.spec_from_file_location(
    "validate_branch_b_draft_under_test", ROOT / "scripts" / "validate_branch_b_draft.py")
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def test_draft_folder_and_files_exist():
    assert DRAFT_DIR.is_dir()
    for rel in mod.REQUIRED_FILES:
        assert (ROOT / rel).exists(), f"missing {rel}"


def test_validator_passes():
    assert mod.check(ROOT) == []


def test_readme_marks_draft_not_current_do_not_apply():
    low = (DRAFT_DIR / "README.md").read_text(encoding="utf-8").lower()
    assert "branch b draft" in low
    assert "not the current status" in low
    assert "do not apply" in low


def test_apply_checklist_requires_gate_evidence():
    low = (DRAFT_DIR / "branch_b_apply_checklist.md").read_text(encoding="utf-8").lower()
    assert "run_playwright_gate.py" in low and "exit 0" in low
    assert "engine=playwright" in low
    assert "is_real_browser=true" in low
    assert "screenshot" in low
    assert "no lingering" in low


def test_planning_note_forces_playwright_and_forbids_fallback():
    low = (DRAFT_DIR / "read_browser_console_v1_planning_note.md").read_text(encoding="utf-8").lower()
    assert "browser_mode=playwright" in low
    assert "http_fallback" in low
    assert ("forbidden" in low) or ("not allowed" in low)


def test_all_patch_files_marked_do_not_apply():
    for rel in mod.PATCH_FILES:
        low = (ROOT / rel).read_text(encoding="utf-8").lower()
        assert "draft" in low, rel
        assert "not automatically applied" in low, rel


def test_no_read_browser_console_candidate_created():
    # The planning note must not have spawned an actual candidate.
    assert not list((ROOT / "harnesses" / "candidates").glob("read_browser_console*"))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
