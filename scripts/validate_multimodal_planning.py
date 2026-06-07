"""Validate the Multimodal / Data Channels planning docs (story_multimodal_channel_v0).

Planning gate only — this checks the planning doc set exists and writes down the hard
isolation boundaries; no runtime channel is implemented or expected.

Usable standalone (`python scripts/validate_multimodal_planning.py`) and imported by
`scripts/validate_workflows.py` via `_module_errors(root, "validate_multimodal_planning")`.
"""
from __future__ import annotations

from pathlib import Path

MM_DIR = "docs/multimodal_data_channels"

REQUIRED_FILES = [
    f"{MM_DIR}/README.md",
    f"{MM_DIR}/source_isolation_model.md",
    f"{MM_DIR}/untrusted_content_policy.md",
    f"{MM_DIR}/artifact_storage_policy.md",
    f"{MM_DIR}/eval_plan.md",
    "reports/story_multimodal_channel_v0/README.md",
]

# Hard boundaries that must appear across the planning docs (case-insensitive).
REQUIRED_PHRASES = [
    "planning only",
    "no runtime implementation",
    "no new data channel implemented",
    "source isolation",
    "data, not instruction",
    "browser content cannot trigger tool / repair / promotion",
    "must be redacted",
    "each channel requires its own eval",
    "no secret in artifacts",
    "no stable modification",
    "no raw shell",
    "no real api",
]


def check(root: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing multimodal planning path: {rel}")

    combined = ""
    for rel in REQUIRED_FILES:
        p = root / rel
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for phrase in REQUIRED_PHRASES:
        if phrase not in combined:
            errors.append(f"multimodal planning docs missing phrase: {phrase!r}")

    # The story must be marked done/completed.
    story = root / "docs/epics/stories/story_multimodal_channel_v0.md"
    if story.exists():
        low = story.read_text(encoding="utf-8").lower()
        if "done" not in low and "completed" not in low:
            errors.append("story_multimodal_channel_v0.md not marked done/completed")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("[FAIL] multimodal planning docs incomplete:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] multimodal planning docs complete (planning only; isolation documented)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
