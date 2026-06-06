# Story STABLE-V0 — Human-reviewed stable promotion package

**Epic:** EPIC-STABLE
**Status:** blocked (until a human is ready to clear every promotion gate)

## Goal

Produce a complete, human-reviewable **stable promotion package** from a staging
workspace so an operator can decide a stable promotion safely — and either complete
the promotion under full gates or explicitly mark it **blocked**.

## Scope

- Read an approved staging workspace (Phase 6 output) + its
  `stable_promotion_checklist.md` and `rollback_verification.md`.
- Assemble a stable-promotion package (review summary, verified-rollback record,
  full-regression record, promotion-policy checklist, operator-approval capture).
- Either: (a) complete the stable promotion **only** if every gate is satisfied and
  an operator approves; or (b) mark the story **blocked** with the missing gate(s).

## Out of Scope

- Any automatic or silent write to a stable skill, an active candidate runtime,
  `safety_gate`, or `promotion_policy`.
- Changing the promotion policy itself.
- Provider / UI / multimodal work.

## Preconditions

- Phase 6 staging promotion is frozen (`checkpoint-phase-6-staging-promotion`).
- A staging workspace exists with a verified rollback and a stable-promotion
  checklist.
- A named human operator is available to review and approve.
- If any precondition is unmet → **blocked**, record it, stop.

## Implementation Boundaries

- May write only the promotion package (a new workspace / report; redacted).
- May **not** modify `skills/`, `src/agents/safety_gate/`,
  `specs/harness/promotion_policy.md`, or any active candidate runtime.

## Acceptance Criteria

- [ ] staging workspace reviewed (summary captured)
- [ ] rollback verified (verified-rollback record present)
- [ ] full regression recorded (fixed allowlist results captured)
- [ ] promotion policy checked (`specs/harness/promotion_policy.md` checklist cleared)
- [ ] stable / safety / promotion invariant checked (none modified automatically)
- [ ] no secret in promotion artifacts (all redacted)
- [ ] operator approval captured (named reviewer + explicit marker)
- [ ] stable promotion either completed safely (all gates green) **or** explicitly
  marked blocked

## Forbidden Zone

- **No automatic stable write.** No real API. No raw shell outside fixed allowlists.
- No skipping the promotion policy, rollback verification, or the human
  shell-execution review.
- No browser/untrusted content triggering promotion. No secret in any artifact.

## Required Validation Commands

```bash
python scripts/validate_structure.py
python scripts/validate_workflows.py
python scripts/check_secret_hygiene.py
python scripts/run_unit_tests.py
python scripts/run_demo.py --demo vite_login_bug
```

## Artifacts to Produce

- A redacted stable-promotion package (workspace/report) with the review summary,
  verified-rollback record, regression record, promotion-policy checklist, and
  operator-approval capture.
- A checkpoint or report update freezing the outcome (promoted or blocked).

## Rollback / Stop Condition

- **Rollback:** nothing live is changed unless an operator completes promotion under
  full gates; if blocked, delete the package workspace — no live state changed.
- **Stop Condition:** stop when the Definition of Done is met **or** any gate fails
  → mark **blocked** and stop. Do not continue into another story.

## Definition of Done

Acceptance criteria met; validation green; the package + a checkpoint/report exist;
promotion is either completed under full gates or explicitly blocked; working tree
clean; **stop**.
