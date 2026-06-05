import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

REPORT_DIR = ROOT / "reports" / "phase_0_to_1_harness_mvp"
README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"

_spec = importlib.util.spec_from_file_location(
    "validate_phase_report_under_test", ROOT / "scripts" / "validate_phase_report.py")
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def test_report_folder_and_all_files_exist():
    assert REPORT_DIR.is_dir()
    for rel in mod.REQUIRED_REPORT_FILES:
        assert (ROOT / rel).exists(), f"missing {rel}"


def test_validator_passes():
    assert mod.check(ROOT) == []


def test_report_readme_links_checkpoint():
    text = (REPORT_DIR / "README.md").read_text(encoding="utf-8").lower()
    assert "checkpoint-0-to-1-harness-gates" in text


def test_risks_doc_states_key_flags():
    text = (REPORT_DIR / "08_risks_and_limitations.md").read_text(encoding="utf-8").lower()
    assert "http_fallback is not a real browser" in text
    assert "read_browser_console is blocked" in text


def test_next_phase_has_playwright_gate():
    text = (REPORT_DIR / "09_next_phase_plan.md").read_text(encoding="utf-8").lower()
    assert "playwright real browser gate" in text


def test_artifact_index_lists_quick_resume():
    text = (REPORT_DIR / "12_artifact_index.md").read_text(encoding="utf-8")
    assert "docs/quick_resume.md" in text


def test_presentation_outline_exists():
    assert (REPORT_DIR / "10_presentation_outline.md").exists()


def test_root_readme_and_quick_resume_link_report():
    assert "reports/phase_0_to_1_harness_mvp/README.md" in README.read_text(encoding="utf-8")
    assert "reports/phase_0_to_1_harness_mvp/README.md" in QUICK_RESUME.read_text(encoding="utf-8")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
