import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHECKPOINT = ROOT / "docs" / "checkpoints" / "checkpoint-phase-1b-full-browser-e2e.md"
README = ROOT / "README.md"
QUICK = ROOT / "docs" / "quick_resume.md"
MATRIX = ROOT / "docs" / "candidate_status_matrix.md"
PROMOTION = ROOT / "docs" / "promotion_readiness_review.md"
PHASE1 = ROOT / "reports" / "phase_1_real_browser_gate" / "README.md"
DEMO = ROOT / "reports" / "phase_1_real_browser_gate" / "02_demo_script_full_browser_e2e.md"
DIAGRAM = ROOT / "reports" / "phase_1_real_browser_gate" / "03_architecture_diagram_full_chain.md"
_LINK = "checkpoint-phase-1b-full-browser-e2e"


def test_checkpoint_exists_with_frozen_state():
    assert CHECKPOINT.exists()
    low = CHECKPOINT.read_text(encoding="utf-8").lower()
    for needle in ("checkpoint-phase-1b-full-browser-e2e", "b7fa1d5", "score = 1.0",
                   "engine=playwright", "is_real_browser=true",
                   "patch_applied = true", "tests_pass = true",
                   "browser_reverify_passed = true",
                   "no_fatal_console_error_after_patch = true",
                   "pre-patch console counts", "post-patch console counts",
                   "active overrides", "remaining risks"):
        assert needle in low, needle
    # decision-point phases listed
    for needle in ("llm planner", "auto-repair", "ui dashboard", "multimodal"):
        assert needle in low, needle
    # frozen constraints
    assert "stable skills / safety_gate / promotion_policy untouched" in low


def test_readme_and_quick_resume_link_phase_1b():
    assert _LINK in README.read_text(encoding="utf-8")
    assert _LINK in QUICK.read_text(encoding="utf-8")


def test_matrix_full_browser_passed():
    text = MATRIX.read_text(encoding="utf-8")
    row = ""
    for line in text.splitlines():
        if line.lstrip().startswith("| `full_browser_vite_login_bug_e2e`"):
            row = line
    assert row, "full_browser_vite_login_bug_e2e row not found"
    assert "passed" in row.lower()


def test_promotion_says_stable_still_needs_review():
    assert "stable promotion still needs" in PROMOTION.read_text(encoding="utf-8").lower()


def test_phase1_report_demo_and_diagram_exist():
    assert PHASE1.exists() and DEMO.exists() and DIAGRAM.exists()
    low = PHASE1.read_text(encoding="utf-8").lower()
    assert "full browser e2e" in low and "passed" in low
    demo = DEMO.read_text(encoding="utf-8")
    assert "run_full_browser_gate.py" in demo
    diagram = DIAGRAM.read_text(encoding="utf-8").lower()
    assert "mermaid" in diagram


def test_candidate_docs_validator_passes():
    spec = importlib.util.spec_from_file_location(
        "vcd_1b", ROOT / "scripts" / "validate_candidate_docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check(ROOT) == []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
