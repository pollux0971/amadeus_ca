"""Validate the Project Report (project_report/).

Checks the 12 report sections exist, the required elements are present (architecture
diagram, phase timeline, evaluation table, safety section, future work, presentation
script), and that the stable-promotion audit result is written as NO-GO / BLOCKED
(never as completed).

Usable standalone (`python scripts/validate_project_report.py`) and imported by
`scripts/validate_workflows.py` via `_module_errors(root, "validate_project_report")`.
"""
from __future__ import annotations

from pathlib import Path

PR = "project_report"

REQUIRED_FILES = [
    f"{PR}/README.md",
    f"{PR}/01_abstract.md",
    f"{PR}/02_motivation_and_problem.md",
    f"{PR}/03_system_architecture.md",
    f"{PR}/04_harness_engineering_method.md",
    f"{PR}/05_implementation_phases.md",
    f"{PR}/06_evaluation_and_results.md",
    f"{PR}/07_safety_and_risk_management.md",
    f"{PR}/08_demo_and_dashboard.md",
    f"{PR}/09_limitations.md",
    f"{PR}/10_future_work.md",
    f"{PR}/11_conclusion.md",
    f"{PR}/12_presentation_script.md",
    "reports/project_report_v1/README.md",
]

# Boundary / content phrases that must appear across the report.
REQUIRED_PHRASES = [
    "harness engineering",
    "browser",
    "fake provider",
    "execution bridge",
    "repair proposal",
    "candidate merge",
    "staging",
    "dashboard",
    "demo package",
    "no real api",
    "password_and_api.txt",
    "no raw shell",
    "no stable modification",
    "browser content cannot trigger tool / repair / promotion",
]


def check(root: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing project report path: {rel}")

    def _read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    # Required structural elements in specific sections.
    arch = _read(f"{PR}/03_system_architecture.md").lower()
    if "```mermaid" not in arch and "flowchart" not in arch and "fakellmprovider" not in arch:
        errors.append("03_system_architecture.md missing an architecture diagram")
    timeline = _read(f"{PR}/05_implementation_phases.md").lower()
    if "phase timeline" not in timeline or "phase 1b" not in timeline or "phase 6" not in timeline:
        errors.append("05_implementation_phases.md missing the phase timeline")
    results = _read(f"{PR}/06_evaluation_and_results.md").lower()
    if "results table" not in results or "453" not in results:
        errors.append("06_evaluation_and_results.md missing the results table")
    script = _read(f"{PR}/12_presentation_script.md").lower()
    if "presentation script" not in script or "[0:00" not in script:
        errors.append("12_presentation_script.md missing the 5-8 min presentation script")

    # Combined boundary phrases.
    combined = "\n".join(_read(rel).lower() for rel in REQUIRED_FILES)
    for phrase in REQUIRED_PHRASES:
        if phrase not in combined:
            errors.append(f"project report missing phrase: {phrase!r}")

    # Stable promotion audit must be written as NO-GO / BLOCKED, never completed.
    if "no-go" not in combined and "blocked" not in combined:
        errors.append("project report must record the stable promotion audit as NO-GO / BLOCKED")
    for bad in ("stable promotion completed", "stable promotion is complete",
                "stable promotion done", "promoted to stable"):
        if bad in combined:
            errors.append(f"project report falsely claims {bad!r}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("[FAIL] project report incomplete:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] project report complete (diagram + timeline + results + safety + script)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
