# Repair Proposal

> **PROPOSAL ONLY — NOT APPLIED — HUMAN APPROVAL REQUIRED**

- proposal id: repair_test_failed
- failure_type: test_failed
- marker: FAKE_REPAIR_TEST_FAILED
- applied: **false**
- valid: True

**Rationale:** Tests failed after the change; propose a candidate-side fix and a regression test. No patch is applied (PROPOSAL ONLY).

| id | action_type | target | risk | approval | tests_to_run |
| --- | --- | --- | --- | --- | --- |
| a1 | update_candidate | harnesses/candidates/<candidate-id>/ | medium | no | tests/unit/, evals/ |
| a2 | add_test | tests/unit/test_regression_after_fix.py | low | no | tests/unit/test_regression_after_fix.py |

## Action reasons
- **a1** (update_candidate): Propose a minimal fix in the candidate so its tests pass.
- **a2** (add_test): Add a regression test that locks the fixed behavior.

> This is a proposal only. Nothing here is applied, executed, or promoted.
> A human must review and approve before any change is made.
