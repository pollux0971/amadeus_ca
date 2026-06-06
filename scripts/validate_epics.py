"""Validate the Epic / Story backlog under docs/epics/.

Checks that the backlog exists and that the bounded-story discipline + hard
boundaries are written down:
  - docs/epics/README.md, epic_overview.md, 4 epics, 4 stories, story_template.md,
    decision_matrix.md all exist;
  - each story declares Acceptance Criteria / Forbidden Zone / Validation Commands /
    Stop Condition;
  - README + quick_resume link the backlog;
  - the backlog states one-bounded-story + no real API / no stable modification /
    no raw shell / no secret.

Usable standalone (`python scripts/validate_epics.py`) and imported by
`scripts/validate_workflows.py` via `_module_errors(root, "validate_epics")`.
"""
from __future__ import annotations

from pathlib import Path

EPICS_DIR = "docs/epics"

REQUIRED_FILES = [
    f"{EPICS_DIR}/README.md",
    f"{EPICS_DIR}/epic_overview.md",
    f"{EPICS_DIR}/epic_stable_promotion.md",
    f"{EPICS_DIR}/epic_ui_dashboard.md",
    f"{EPICS_DIR}/epic_real_provider.md",
    f"{EPICS_DIR}/epic_multimodal_data_channels.md",
    f"{EPICS_DIR}/story_template.md",
    f"{EPICS_DIR}/decision_matrix.md",
    f"{EPICS_DIR}/stories/story_stable_promotion_v0.md",
    f"{EPICS_DIR}/stories/story_ui_dashboard_v0.md",
    f"{EPICS_DIR}/stories/story_real_provider_v0.md",
    f"{EPICS_DIR}/stories/story_multimodal_channel_v0.md",
]

STORY_FILES = [f for f in REQUIRED_FILES if "/stories/" in f]

# Each story must declare these (case-insensitive).
REQUIRED_STORY_SECTIONS = [
    "acceptance criteria",
    "forbidden zone",
    "validation commands",
    "stop condition",
]

# The backlog (combined docs/epics text) must state these constraints.
REQUIRED_BACKLOG_PHRASES = [
    "one bounded story",
    "no real api",
    "no stable modification",
    "no raw shell",
    "no secret",
]

# README + quick_resume must link the backlog.
EPICS_LINK = "docs/epics"


def check(root: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing epics path: {rel}")

    # Per-story required sections.
    for rel in STORY_FILES:
        p = root / rel
        if not p.exists():
            continue  # already reported above
        low = p.read_text(encoding="utf-8").lower()
        for section in REQUIRED_STORY_SECTIONS:
            if section not in low:
                errors.append(f"{rel} missing required section: {section!r}")

    # Backlog-wide constraint phrases (combined epics text).
    combined = ""
    for rel in REQUIRED_FILES:
        p = root / rel
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for phrase in REQUIRED_BACKLOG_PHRASES:
        if phrase not in combined:
            errors.append(f"epics docs missing constraint phrase: {phrase!r}")

    # README + quick_resume must link the backlog.
    for doc in ("README.md", "docs/quick_resume.md"):
        p = root / doc
        if not p.exists():
            errors.append(f"missing doc: {doc}")
            continue
        if EPICS_LINK not in p.read_text(encoding="utf-8"):
            errors.append(f"{doc} missing epics link ({EPICS_LINK!r})")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("[FAIL] epics backlog incomplete:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] epics backlog is complete (one bounded story; boundaries documented)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
