"""Validate the Project Demo Package (demo_package/).

Checks the 9 demo docs exist, that the key boundary statements are written down, and
that the demo command list contains NO real-API / secret-file / stable-promotion
command.

Usable standalone (`python scripts/validate_demo_package.py`) and imported by
`scripts/validate_workflows.py` via `_module_errors(root, "validate_demo_package")`.
"""
from __future__ import annotations

from pathlib import Path

DP = "demo_package"

REQUIRED_FILES = [
    f"{DP}/README.md",
    f"{DP}/01_project_overview.md",
    f"{DP}/02_architecture_summary.md",
    f"{DP}/03_demo_commands.md",
    f"{DP}/04_dashboard_demo.md",
    f"{DP}/05_phase_timeline.md",
    f"{DP}/06_safety_boundaries.md",
    f"{DP}/07_next_steps.md",
    f"{DP}/08_teacher_presentation_outline.md",
    "reports/demo_package_v0/README.md",
]

# Boundary statements that must appear across the package (case-insensitive).
REQUIRED_PHRASES = [
    "read-only dashboard",
    "stable promotion",          # together with "blocked" below
    "no real api",
    "password_and_api.txt",
    "no raw shell",
    "no stable modification",
    "bounded story",
    "browser content cannot trigger tool / repair / promotion",
]

# The demo command list (03) must NOT contain any of these (real API / secret /
# stable promotion). We look for risky command-ish tokens, not mere prose mentions —
# but to stay strict we forbid these substrings outright in 03_demo_commands.md
# *command lines* are the only place they would appear as runnable commands.
FORBIDDEN_IN_COMMANDS = [
    "llm_provider=openai",
    "llm_provider=anthropic",
    "--enable-real-api",
    "stable_promote",
    "promote_to_stable",
    "cat /data/python/computer_agent_v5/password_and_api.txt",
    "cat .env",
]


def check(root: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing demo package path: {rel}")

    combined = ""
    for rel in REQUIRED_FILES:
        p = root / rel
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"

    for phrase in REQUIRED_PHRASES:
        if phrase not in combined:
            errors.append(f"demo package missing phrase: {phrase!r}")
    # "stable promotion" must be qualified as blocked / not started somewhere.
    if "blocked" not in combined and "not started" not in combined:
        errors.append("demo package must state stable promotion is blocked/not started")

    # Demo command list must contain no real-API / secret / stable-promotion command.
    cmds = root / f"{DP}/03_demo_commands.md"
    if cmds.exists():
        low = cmds.read_text(encoding="utf-8").lower()
        for bad in FORBIDDEN_IN_COMMANDS:
            if bad in low:
                errors.append(f"03_demo_commands.md contains forbidden command: {bad!r}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("[FAIL] demo package incomplete:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] demo package complete (safe demo commands; boundaries documented)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
