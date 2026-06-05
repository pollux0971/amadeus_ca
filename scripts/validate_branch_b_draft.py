"""Validate the Branch B (Playwright-gate-passed) draft pack.

Checks the draft folder + 7 files exist, that they are clearly marked as drafts /
not-current / do-not-apply, that the apply checklist and planning note carry the
required content, and that every *.patch.md carries draft wording. Usable
standalone and imported by scripts/validate_workflows.py.
"""
from __future__ import annotations

from pathlib import Path

DRAFT_DIR = "docs/branch_b_playwright_gate_passed_draft"

REQUIRED_FILES = [
    f"{DRAFT_DIR}/README.md",
    f"{DRAFT_DIR}/candidate_status_matrix.patch.md",
    f"{DRAFT_DIR}/promotion_readiness_review.patch.md",
    f"{DRAFT_DIR}/next_milestone_plan.patch.md",
    f"{DRAFT_DIR}/quick_resume.patch.md",
    f"{DRAFT_DIR}/read_browser_console_v1_planning_note.md",
    f"{DRAFT_DIR}/branch_b_apply_checklist.md",
]

PATCH_FILES = [f for f in REQUIRED_FILES if f.endswith(".patch.md")]

REQUIRED_SUBSTRINGS = {
    f"{DRAFT_DIR}/README.md": ["branch b draft", "not the current status", "do not apply"],
    f"{DRAFT_DIR}/branch_b_apply_checklist.md": [
        "run_playwright_gate.py", "exit 0", "engine=playwright",
    ],
    f"{DRAFT_DIR}/read_browser_console_v1_planning_note.md": [
        "browser_mode=playwright",
        "http_fallback",
    ],
}


def check(root: Path) -> list[str]:
    errors: list[str] = []

    if not (root / DRAFT_DIR).is_dir():
        errors.append(f"missing draft folder: {DRAFT_DIR}/")
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing draft file: {rel}")

    for rel, needles in REQUIRED_SUBSTRINGS.items():
        path = root / rel
        if not path.exists():
            errors.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        for needle in needles:
            if needle.lower() not in text:
                errors.append(f"{rel} missing required substring: '{needle}'")

    # planning note must forbid the http_fallback console.
    note = root / f"{DRAFT_DIR}/read_browser_console_v1_planning_note.md"
    if note.exists():
        low = note.read_text(encoding="utf-8").lower()
        if "forbidden" not in low and "not allowed" not in low:
            errors.append("planning note must state http_fallback is forbidden / not allowed")

    # every *.patch.md must carry draft / not-automatically-applied wording.
    for rel in PATCH_FILES:
        path = root / rel
        if not path.exists():
            continue
        low = path.read_text(encoding="utf-8").lower()
        if "not automatically applied" not in low or "draft" not in low:
            errors.append(f"{rel} must carry 'draft' + 'not automatically applied' wording")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("[FAIL] Branch B draft pack incomplete:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] Branch B draft pack is complete (and marked do-not-apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
