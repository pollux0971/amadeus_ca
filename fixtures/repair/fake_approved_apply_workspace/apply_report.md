# Apply Report

> **APPROVED APPLICATION WORKSPACE ONLY**
> **NOT PROMOTED**
> **STABLE UNTOUCHED**
> **HUMAN REVIEW STILL REQUIRED FOR MERGE/PROMOTION**

- apply id: fixture_apply
- proposal id: repair_test_failed
- approved by: fixture-human-reviewer
- promoted: **False**
- stable modified: **False**
- apply validation passed: **True**

## Proposed changes (in this workspace only)
| action id | action_type | intended target | proposed file |
| --- | --- | --- | --- |
| a1 | update_candidate | harnesses/candidates/<candidate-id>/ | proposed_changes/candidate/harnesses__candidates__<candidate-id>__.patch_note.md |
| a2 | add_test | tests/unit/test_regression_after_fix.py | proposed_changes/tests/tests__unit__test_regression_after_fix.py.py |

## Targeted tests (fixed allowlist)
- executed: **False**
  - `python scripts/validate_structure.py`
  - `python scripts/validate_workflows.py`
  - `python scripts/run_unit_tests.py`
  - `python scripts/run_demo.py --demo vite_login_bug`

> This apply workspace modifies no repo target file, promotes nothing, and
> touches no stable skill / safety gate / promotion policy. A human must
> review and merge separately; merge and promotion are future phases.
