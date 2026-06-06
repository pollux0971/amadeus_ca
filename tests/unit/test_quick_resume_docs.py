import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"


def test_quick_resume_doc_exists():
    assert QUICK_RESUME.exists()


def test_readme_has_candidate_status_and_gate_chain_index():
    text = README.read_text(encoding="utf-8")
    low = text.lower()
    assert "## current harness candidate status" in low
    assert "## gate chain" in low
    # links to the key docs/evals/scripts
    for target in (
        "docs/candidate_status_matrix.md",
        "docs/promotion_readiness_review.md",
        "docs/next_milestone_plan.md",
        "evals/browser/open_localhost_playwright_required_smoke.yaml",
        "evals/browser/full_browser_vite_login_bug_e2e.yaml",
        "scripts/run_playwright_gate.py",
        "scripts/run_full_browser_gate.py",
    ):
        assert target in text, f"README missing link to {target}"


def test_readme_states_key_flags():
    low = README.read_text(encoding="utf-8").lower()
    assert "http_fallback is not a real browser" in low
    # Phase 1B: the full real-browser e2e is green and linked.
    assert "full_browser_vite_login_bug_e2e is green" in low
    assert "checkpoint-phase-1b-full-browser-e2e" in low
    assert "staging-ready" in low


def test_quick_resume_has_resume_essentials():
    low = QUICK_RESUME.read_text(encoding="utf-8").lower()
    assert "active overrides" in low
    assert "run_playwright_gate.py --dry-run" in low
    assert "run_full_browser_gate.py --dry-run" in low
    assert "checkpoint-phase-1b-full-browser-e2e" in low
    # the actual active overrides are listed
    assert "open_localhost_browser_v1" in low
    assert "patch_file_and_run_tests_v2" in low
    assert "start_local_server_v1" in low


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
