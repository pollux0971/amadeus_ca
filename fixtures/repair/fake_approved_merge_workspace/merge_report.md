# Merge Report

> **CANDIDATE WORKSPACE MERGE ONLY**
> **STABLE UNTOUCHED**
> **NOT PROMOTED**
> **HUMAN REVIEW REQUIRED BEFORE STAGING/STABLE**
> **ROLLBACK PLAN INCLUDED**

- merge id: fixture_merge
- source apply workspace: fixtures/repair/fake_approved_apply_workspace
- reviewer: fixture-merge-reviewer
- merged to candidate workspace: **True**
- stable modified: **False**
- promoted: **False**
- rollback available: **True**
- merge validation passed: **True**

## Merged changes (in this candidate workspace only)
- `merged_changes/candidate/harnesses__candidates__<candidate-id>__.patch_note.md`
- `merged_changes/tests/tests__unit__test_regression_after_fix.py.py`

## Targeted tests + regression (fixed allowlist)
- executed: **False**
- targeted:
  - `python scripts/validate_structure.py`
  - `python scripts/validate_workflows.py`
  - `python scripts/run_unit_tests.py`
- regression:
  - `python scripts/run_demo.py --demo vite_login_bug`
  - `python scripts/run_eval.py --task evals/repair/fake_approved_patch_application.yaml`
  - `python scripts/run_eval.py --task evals/repair/fake_repair_proposal_only.yaml`

> This merge lands ONLY in a candidate merge workspace. No repo target file,
> active candidate, stable skill, safety gate, or promotion policy is
> modified, and nothing is promoted. A rollback plan is included; a human
> must review before any staging/stable promotion.
