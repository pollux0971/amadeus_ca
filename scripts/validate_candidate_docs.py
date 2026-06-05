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
]

# Non-doc artifacts the gate depends on.
REQUIRED_FILES = [
    "evals/browser/open_localhost_playwright_required_smoke.yaml",
    "scripts/run_playwright_gate.py",
]

# Each rule passes if ALL of its substrings appear in the combined doc text
# (case-insensitive). Phrased as a short description -> required substrings.
REQUIRED_STATEMENTS = {
    "read_browser_console is blocked": ["read_browser_console", "blocked"],
    "open_localhost_browser requires a Playwright gate": ["open_localhost_browser", "playwright"],
    "http_fallback is not a real browser": ["http_fallback is not a real browser"],
}

# Specific files must contain specific substrings (case-insensitive).
REQUIRED_FILE_SUBSTRINGS = {
    "docs/next_milestone_plan.md": ["run_playwright_gate.py"],
    "docs/candidate_status_matrix.md": ["open_localhost_browser", "playwright"],
    "evals/browser/open_localhost_playwright_required_smoke.yaml": [
        "browser_mode: playwright", "require_real_browser: true",
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
