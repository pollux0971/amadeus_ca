# Approval checklist (must be cleared by a human before any apply)

> PROPOSAL ONLY — NOT APPLIED — HUMAN APPROVAL REQUIRED

- proposal id: `repair_test_failed`
- failure_type: `test_failed`
- validation passed: **True**

This is a FAKE, redacted approval checklist fixture used to exercise the approved
patch application pipeline. It contains no secret.

## Required sign-offs

- [x] A human reviewed every proposed action and target.
- [x] No action targets a stable skill, the safety gate, or the promotion policy.
- [x] No action is a raw shell / direct command / delete.
- [x] All targets stay inside the allowed roots (candidates/tests/evals/docs/reports).
- [x] High-risk actions have explicit approval.
- [x] The proposal contains no secret.
- [x] The change will be made in a candidate workspace, NOT in stable.
- [x] Promotion (if any) follows `specs/harness/promotion_policy.md` separately.

## Explicit apply approval

APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY: true
Reviewer: fixture-human-reviewer

> The marker above plus a named reviewer authorizes apply to a candidate
> **apply workspace only** — never to stable, and never a promotion.
