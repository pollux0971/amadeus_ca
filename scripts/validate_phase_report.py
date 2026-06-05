"""Validate the phase report pack (reports/phase_0_to_1_harness_mvp/).

Checks the report folder and its files exist and contain the key statements, and
that the root README + quick_resume link to it. Usable standalone and imported by
scripts/validate_workflows.py.
"""
from __future__ import annotations

from pathlib import Path

REPORT_DIR = "reports/phase_0_to_1_harness_mvp"

REQUIRED_REPORT_FILES = [
    f"{REPORT_DIR}/README.md",
    f"{REPORT_DIR}/01_project_overview.md",
    f"{REPORT_DIR}/02_system_architecture.md",
    f"{REPORT_DIR}/03_workflow_zero_to_one.md",
    f"{REPORT_DIR}/04_candidate_evolution_summary.md",
    f"{REPORT_DIR}/05_demo_script.md",
    f"{REPORT_DIR}/06_architecture_diagrams.md",
    f"{REPORT_DIR}/07_evaluation_results.md",
    f"{REPORT_DIR}/08_risks_and_limitations.md",
    f"{REPORT_DIR}/09_next_phase_plan.md",
    f"{REPORT_DIR}/10_presentation_outline.md",
    f"{REPORT_DIR}/11_teacher_explanation.md",
    f"{REPORT_DIR}/12_artifact_index.md",
]

# file -> required substrings (case-insensitive).
REQUIRED_SUBSTRINGS = {
    f"{REPORT_DIR}/README.md": ["checkpoint-0-to-1-harness-gates"],
    f"{REPORT_DIR}/08_risks_and_limitations.md": [
        "http_fallback is not a real browser", "read_browser_console is blocked",
    ],
    f"{REPORT_DIR}/09_next_phase_plan.md": ["playwright real browser gate"],
    f"{REPORT_DIR}/12_artifact_index.md": ["docs/quick_resume.md"],
    "README.md": [f"{REPORT_DIR}/readme.md"],  # Phase Reports link
    "docs/quick_resume.md": ["reports/phase_0_to_1_harness_mvp/readme.md"],  # phase report link
}


def check(root: Path) -> list[str]:
    errors: list[str] = []

    if not (root / REPORT_DIR).is_dir():
        errors.append(f"missing report folder: {REPORT_DIR}/")
    for rel in REQUIRED_REPORT_FILES:
        if not (root / rel).exists():
            errors.append(f"missing report file: {rel}")

    for rel, needles in REQUIRED_SUBSTRINGS.items():
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
        print("[FAIL] phase report incomplete:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] phase report pack is complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
