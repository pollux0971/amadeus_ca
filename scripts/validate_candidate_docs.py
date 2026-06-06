"""Validate the candidate status / promotion / milestone docs.

Checks that the three planning docs exist and that the key policy statements are
present somewhere across them:
  - read_browser_console is blocked
  - open_localhost_browser requires a Playwright gate
  - http_fallback is not a real browser

Usable standalone (`python scripts/validate_candidate_docs.py`) and imported by
`scripts/validate_workflows.py`.
"""
from __future__ import annotations

from pathlib import Path

REQUIRED_DOCS = [
    "docs/candidate_status_matrix.md",
    "docs/promotion_readiness_review.md",
    "docs/next_milestone_plan.md",
    "docs/quick_resume.md",
]

# Non-doc artifacts the gates depend on.
REQUIRED_FILES = [
    "evals/browser/open_localhost_playwright_required_smoke.yaml",
    "scripts/run_playwright_gate.py",
    "evals/browser/full_browser_vite_login_bug_e2e.yaml",
    "scripts/run_full_browser_gate.py",
    "docs/checkpoints/checkpoint-0-to-1-harness-gates.md",
    "docs/checkpoints/phase_1a_playwright_gate_passed.md",
    "harnesses/candidates/read_browser_console_v1/candidate.yaml",
    "harnesses/candidates/read_browser_console_v1/SKILL.md",
    "evals/browser/read_browser_console_smoke.yaml",
    "docs/checkpoints/phase_1b_full_browser_gate_passed.md",
    "docs/checkpoints/checkpoint-phase-1b-full-browser-e2e.md",
    "reports/phase_1_real_browser_gate/02_demo_script_full_browser_e2e.md",
    "reports/phase_1_real_browser_gate/03_architecture_diagram_full_chain.md",
]

PHASE_1B = "docs/checkpoints/checkpoint-phase-1b-full-browser-e2e.md"

CHECKPOINT = "docs/checkpoints/checkpoint-0-to-1-harness-gates.md"
GATE_PASSED = "docs/checkpoints/phase_1a_playwright_gate_passed.md"

# Each rule passes if ALL of its substrings appear in the combined doc text
# (case-insensitive). Phrased as a short description -> required substrings.
REQUIRED_STATEMENTS = {
    "read_browser_console is blocked": ["read_browser_console", "blocked"],
    "open_localhost_browser + Playwright recorded": ["open_localhost_browser", "playwright"],
    "http_fallback is not a real browser": ["http_fallback is not a real browser"],
    # Branch B applied: open_localhost_browser_v1 is staging-ready, but the full
    # browser e2e stays blocked until a read_browser_console candidate exists.
    "open_localhost_browser_v1 staging-ready": ["open_localhost_browser_v1", "staging-ready"],
    "full browser e2e passed": ["full_browser_vite_login_bug_e2e", "passed"],
}

# Specific files must contain specific substrings (case-insensitive).
REQUIRED_FILE_SUBSTRINGS = {
    "docs/next_milestone_plan.md": [
        "run_playwright_gate.py", "run_full_browser_gate.py",
        "read_browser_console_v1", "browser_mode=playwright",
    ],
    "docs/candidate_status_matrix.md": ["open_localhost_browser", "playwright", "staging-ready"],
    GATE_PASSED: [
        "engine=playwright", "is_real_browser", "staging-ready",
        "read_browser_console", "blocked",
    ],
    # read_browser_console_v1 must be a real-browser-only console (no fake console).
    "harnesses/candidates/read_browser_console_v1/SKILL.md": [
        "browser_mode", "playwright", "http_fallback_not_allowed",
    ],
    "evals/browser/open_localhost_playwright_required_smoke.yaml": [
        "browser_mode: playwright", "require_real_browser: true",
    ],
    "evals/browser/full_browser_vite_login_bug_e2e.yaml": [
        "browser_mode: playwright", "require_real_browser: true",
        "read_browser_console", "no_fatal_console_error_after_patch",
    ],
    "README.md": [
        "current harness candidate status",
        "gate chain",
        "http_fallback is not a real browser",
        "checkpoint-phase-1b-full-browser-e2e",  # Phase 1B checkpoint link
    ],
    "docs/quick_resume.md": [
        "active overrides",
        "run_playwright_gate.py --dry-run",
        "run_full_browser_gate.py --dry-run",
        "checkpoint-phase-1b-full-browser-e2e",  # Phase 1B checkpoint link
    ],
    "reports/phase_1_real_browser_gate/README.md": ["full browser e2e", "passed"],
    "docs/promotion_readiness_review.md": ["stable promotion still needs"],
    PHASE_1B: [
        "checkpoint-phase-1b-full-browser-e2e", "b7fa1d5", "engine=playwright",
        "is_real_browser=true", "no_fatal_console_error_after_patch",
    ],
    CHECKPOINT: [
        "patch_file_and_run_tests_v2",
        "start_local_server_v1.2",
        "open_localhost_browser_v1",
        "read_browser_console",
        "blocked",
        "http_fallback is not a real browser",
    ],
}


def check(root: Path) -> list[str]:
    errors: list[str] = []

    missing = [d for d in REQUIRED_DOCS if not (root / d).exists()]
    for d in missing:
        errors.append(f"missing doc: {d}")
    for f in REQUIRED_FILES:
        if not (root / f).exists():
            errors.append(f"missing file: {f}")
    if missing:
        return errors  # can't check doc content if docs are missing

    combined = "\n".join((root / d).read_text(encoding="utf-8") for d in REQUIRED_DOCS).lower()
    for description, needles in REQUIRED_STATEMENTS.items():
        for needle in needles:
            if needle.lower() not in combined:
                errors.append(f"missing statement '{description}': '{needle}' not found in docs")

    for rel, needles in REQUIRED_FILE_SUBSTRINGS.items():
        path = root / rel
        if not path.exists():
            errors.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        for needle in needles:
            if needle.lower() not in text:
                errors.append(f"{rel} missing required substring: '{needle}'")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("[FAIL] candidate docs incomplete:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] candidate status / promotion / milestone docs are complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
