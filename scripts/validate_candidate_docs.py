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

# Each rule passes if ALL of its substrings appear in the combined doc text
# (case-insensitive). Phrased as a short description -> required substrings.
REQUIRED_STATEMENTS = {
    "read_browser_console is blocked": ["read_browser_console", "blocked"],
    "open_localhost_browser requires a Playwright gate": ["open_localhost_browser", "playwright"],
    "http_fallback is not a real browser": ["http_fallback is not a real browser"],
}


def check(root: Path) -> list[str]:
    errors: list[str] = []

    missing = [d for d in REQUIRED_DOCS if not (root / d).exists()]
    for d in missing:
        errors.append(f"missing doc: {d}")
    if missing:
        return errors  # can't check content if files are missing

    combined = "\n".join((root / d).read_text(encoding="utf-8") for d in REQUIRED_DOCS).lower()
    for description, needles in REQUIRED_STATEMENTS.items():
        for needle in needles:
            if needle.lower() not in combined:
                errors.append(f"missing statement '{description}': '{needle}' not found in docs")
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
