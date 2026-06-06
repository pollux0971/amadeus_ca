# Promotion review package — merge `fixture_merge`

> CANDIDATE WORKSPACE MERGE ONLY — STABLE UNTOUCHED — NOT PROMOTED —
> HUMAN REVIEW REQUIRED BEFORE STAGING/STABLE

A human reviewer uses this package to decide whether to take the merged
candidate forward. **Nothing here promotes anything.**

- merge id: `fixture_merge`
- reviewer: fixture-merge-reviewer
- source apply workspace: `fixtures/repair/fake_approved_apply_workspace`
- merged files: 2
- rollback available: True

## Pre-promotion checklist (human must clear)
- [ ] Reviewed every merged change in `merged_changes/`.
- [ ] Targeted tests pass (see `test_results.json` / run the fixed allowlist).
- [ ] Regression suite passes.
- [ ] No stable skill / safety gate / promotion policy is affected.
- [ ] `rollback_plan.md` is sufficient.
- [ ] Promotion (if any) follows `specs/harness/promotion_policy.md`.

## Fixed test allowlist
- targeted:
  - `python scripts/validate_structure.py`
  - `python scripts/validate_workflows.py`
  - `python scripts/run_unit_tests.py`
- regression:
  - `python scripts/run_demo.py --demo vite_login_bug`
  - `python scripts/run_eval.py --task evals/repair/fake_approved_patch_application.yaml`
  - `python scripts/run_eval.py --task evals/repair/fake_repair_proposal_only.yaml`

> Staging/stable promotion is a separate, human-driven phase. This package
> is input to that decision, not the decision itself.
