"""Validate the Stable Promotion Readiness Audit (reports/stable_promotion_readiness_audit_v0/).

Audit only — this checks the audit package exists, gives a clear NO-GO/BLOCKED
recommendation while human gates are unmet, and never claims stable promotion is
completed.

Usable standalone (`python scripts/validate_stable_promotion_audit.py`) and imported
by `scripts/validate_workflows.py` via
`_module_errors(root, "validate_stable_promotion_audit")`.
"""
from __future__ import annotations

from pathlib import Path

AUD = "reports/stable_promotion_readiness_audit_v0"

REQUIRED_FILES = [
    f"{AUD}/README.md",
    f"{AUD}/01_current_state.md",
    f"{AUD}/02_gate_results.md",
    f"{AUD}/03_risk_register.md",
    f"{AUD}/04_go_no_go_recommendation.md",
    f"{AUD}/05_required_human_review.md",
]

# Content that must appear across the audit (case-insensitive).
REQUIRED_PHRASES = [
    "latest checkpoint",
    "phase 1b",
    "phase 6",
    "dashboard",
    "demo package",
    "fake provider",
    "no real api",
    "rollback verification",
    "regression",
    "shell-execution review",
    "operator approval",
    "remaining blocker",
    "stable skills",
    "safety_gate",
    "promotion_policy",
]


def check(root: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing audit path: {rel}")

    combined = ""
    for rel in REQUIRED_FILES:
        p = root / rel
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"

    for phrase in REQUIRED_PHRASES:
        if phrase not in combined:
            errors.append(f"audit missing phrase: {phrase!r}")

    # The recommendation must be NO-GO / BLOCKED while human gates are unmet.
    rec = root / f"{AUD}/04_go_no_go_recommendation.md"
    if rec.exists():
        low = rec.read_text(encoding="utf-8").lower()
        if "no-go" not in low and "blocked" not in low:
            errors.append("04_go_no_go_recommendation.md must state NO-GO / BLOCKED")
        if "go" not in low:
            errors.append("04_go_no_go_recommendation.md missing a go/no-go decision")

    # Must NOT claim stable promotion is completed/done anywhere in the audit.
    for bad in ("stable promotion completed", "stable promotion is complete",
                "stable promotion done", "promoted to stable"):
        if bad in combined:
            errors.append(f"audit falsely claims {bad!r}")

    # Human gates must be flagged as not satisfied / blocking.
    if "not satisfied" not in combined and "not started" not in combined:
        errors.append("audit must flag human gates as not satisfied")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("[FAIL] stable promotion audit incomplete:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] stable promotion readiness audit complete (recommendation: NO-GO/BLOCKED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
