import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MATRIX = ROOT / "docs" / "candidate_status_matrix.md"
PROMOTION = ROOT / "docs" / "promotion_readiness_review.md"
MILESTONE = ROOT / "docs" / "next_milestone_plan.md"
QUICK = ROOT / "docs" / "quick_resume.md"
GATE_PASSED = ROOT / "docs" / "checkpoints" / "phase_1a_playwright_gate_passed.md"
CAND_YAML = ROOT / "harnesses" / "candidates" / "open_localhost_browser_v1" / "candidate.yaml"
CANDIDATES = ROOT / "harnesses" / "candidates"


def _matrix_row(name: str) -> str:
    for line in MATRIX.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(f"| `{name}`"):
            return line
    return ""


def test_candidate_yaml_status_is_staging_ready():
    text = CAND_YAML.read_text(encoding="utf-8")
    assert "status: staging-ready" in text
    # runtime-affecting fields unchanged
    assert "active: true" in text
    assert "version: 1" in text


def test_matrix_open_localhost_row_is_staging_ready():
    row = _matrix_row("open_localhost_browser_v1")
    assert row, "open_localhost_browser_v1 row not found"
    assert "staging-ready" in row.lower()
    assert "real-browser gate" in row.lower()


def test_read_browser_console_v1_exists_dev_real_browser_only():
    # read_browser_console_v1 now exists (started after the gate passed), is dev,
    # and is real-browser-only (no http_fallback).
    cand = CANDIDATES / "read_browser_console_v1" / "candidate.yaml"
    assert cand.exists()
    assert "status: dev" in cand.read_text(encoding="utf-8")
    row = _matrix_row("read_browser_console_v1")
    assert "dev" in row.lower()
    skill = (CANDIDATES / "read_browser_console_v1" / "SKILL.md").read_text(encoding="utf-8")
    assert "http_fallback_not_allowed" in skill
    assert "browser_mode" in skill and "playwright" in skill.lower()


def test_full_browser_gate_still_blocked_and_not_run():
    # A console candidate now exists, but the full browser e2e is still a draft and
    # is NOT run this round (the full chain is not wired yet).
    full = (ROOT / "evals" / "browser" / "full_browser_vite_login_bug_e2e.yaml").read_text(encoding="utf-8")
    assert "draft: true" in full
    assert "blocked_until" in full
    assert "blocked" in _matrix_row("full_browser_vite_login_bug_e2e_draft").lower()


def test_gate_passed_checkpoint_exists_with_flags():
    assert GATE_PASSED.exists()
    low = GATE_PASSED.read_text(encoding="utf-8").lower()
    assert "engine = playwright" in low or "engine=playwright" in low
    assert "is_real_browser = true" in low or "is_real_browser=true" in low
    assert "staging-ready" in low
    assert "read_browser_console" in low and "blocked" in low


def test_http_fallback_is_not_a_real_browser_still_stated():
    combined = "\n".join(
        p.read_text(encoding="utf-8") for p in (MATRIX, PROMOTION, MILESTONE, QUICK)
    ).lower()
    assert "http_fallback is not a real browser" in combined
    # promotion verdict reflects the passed gate
    assert "staging-ready" in PROMOTION.read_text(encoding="utf-8").lower()


def test_milestone_next_is_read_browser_console_playwright():
    low = MILESTONE.read_text(encoding="utf-8").lower()
    assert "read_browser_console_v1" in low
    assert "browser_mode=playwright" in low


def test_candidate_docs_validator_passes():
    spec = importlib.util.spec_from_file_location(
        "vcd", ROOT / "scripts" / "validate_candidate_docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check(ROOT) == []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
