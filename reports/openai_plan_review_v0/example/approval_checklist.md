# Approval Checklist

**NOT APPROVED BY DEFAULT**

**PLAN NOT EXECUTED**

**HUMAN APPROVAL REQUIRED**

- review_status: REVIEW-READY
- APPROVED_FOR_READONLY_EXECUTION: false
- reviewer: (none)

## A human reviewer must confirm ALL before any read-only execution

- [ ] I have read plan.json and plan_summary.md.
- [ ] risk_assessment.md shows overall_risk = low and review_status = REVIEW-READY.
- [ ] Every step uses only an allowlisted read-only skill (v0: inspect_project).
- [ ] execution_preconditions.md are all satisfied.
- [ ] No secret appears in any artifact.
- [ ] I understand the plan is NEVER auto-executed and NEVER auto-repaired.

To approve read-only execution, a human edits the line above to `APPROVED_FOR_READONLY_EXECUTION: true` and sets a non-empty `reviewer:`.
Approval here authorizes ONLY allowlisted read-only execution — never patch, repair, apply, merge, staging, promotion, server, or browser actions.
