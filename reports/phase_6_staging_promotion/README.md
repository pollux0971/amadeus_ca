# Phase 6 — Staging Promotion v0 (Staging Workspace Only)

This phase adds the next safe step after a candidate merge workspace is
**human-approved for staging**: it promotes the merged changes into a **staging
promotion workspace**, with rollback verification, a regression record, and a
stable-promotion checklist. It still does **not** modify stable, an active
candidate, or any real target file, and it does **not** stable-promote. It builds on
Phase 5 (candidate merge).

## Why staging still cannot touch stable

Staging is the last step before "real" stable promotion, so v0 keeps the same hard
boundary and adds only the *staging-workspace* materialization + verification:

- A human must approve staging (marker + named reviewer) **and** pass `--approved`
  with a non-empty `--reviewer`; otherwise staging is refused.
- The promotion lands only in a fresh staging workspace (`staged_changes/`); the
  live repo, active candidates, and stable are never written.
- The rollback plan is **verified** and recorded (`rollback_verification.md`), and a
  `stable_promotion_checklist.md` is produced so a human can decide stable promotion
  safely.
- Nothing is stable-promoted; stable, the safety gate, and the promotion policy are
  untouched, and the promotion policy is still required for any stable move.

This gives a human one place to review the staged candidate, the regression record,
the verified rollback, and the stable-promotion checklist before any stable
decision — without the system ever editing the live tree.

## How a staging workspace is built from an approved merge workspace

```
approved candidate merge workspace (staging_approval_checklist.md: APPROVED_FOR_STAGING_PROMOTION + Reviewer)
  → merge manifest re-validation   (candidate-workspace-only / not promoted / not stable-modified / rollback_available)
  → staging validation             (validate_staging: marker + reviewer + rollback/package present + targets + secret)
  → create staging workspace
        staged_changes/ + staging_manifest.json + staging_report.md +
        rollback_verification.md + regression_results.json + stable_promotion_checklist.md
  → record targeted tests + regression  (fixed allowlist; executed only on --run-tests)
  → stable promotion               NOT in v0
```

Run it:

```bash
# safe preview — validate, print the plan, create no workspace
python scripts/staging_promote.py \
    --merge-workspace fixtures/repair/fake_approved_merge_workspace --dry-run

# promote into a staging workspace (requires --approved + --reviewer)
python scripts/staging_promote.py \
    --merge-workspace fixtures/repair/fake_approved_merge_workspace \
    --approved --reviewer "operator" --staging-id fake_staging_smoke

python scripts/run_eval.py --task evals/repair/fake_staging_promotion.yaml   # → 1.0
```

## Regression / rollback verification

The staging step records a **fixed, hardcoded** test allowlist (never derived from
the merge workspace): targeted (`validate_structure`, `validate_workflows`,
`run_unit_tests`) + regression (`vite_login_bug` demo + the repair/planner evals).
They are recorded in `regression_results.json` by default and executed only on
`--run-tests`. The `rollback_verification.md` confirms the source rollback plan is
present and that rolling back staging is simply deleting the staging workspace.

Frozen at `docs/checkpoints/checkpoint-phase-6-staging-promotion.md` (tag
`checkpoint-phase-6-staging-promotion`). See
`02_demo_script_staging_promotion.md` for a runnable walk-through and
`03_architecture_diagram_staging_promotion.md` for the diagram.

## Results

| Eval / check | Result |
|---|---|
| `fake_staging_promotion` (category `staging_promotion`) | **1.0** |
| `fake_candidate_merge` (Phase 5) | **1.0** (still) |
| `fake_approved_patch_application` (Phase 4) | **1.0** (still) |
| `fake_repair_proposal_only` (Phase 3) | **1.0** (still) |
| `fake_full_browser_plan_execution` (planner execution) | **1.0** (still, real browser) |
| `run_full_browser_gate.py --dry-run` | **safe** |
| `staging_promote.py` without `--approved` / empty `--reviewer` | **rejected** (exit 3) |
| `rollback_verification.md` created | **yes** |
| `stable_promotion_checklist.md` created | **yes** |
| stable files modified | **none** |
| active candidate modified | **none** |
| stable promoted | **false** |
| secret in staging artifacts | **none** (all redacted) |

Success criteria met: `merge_workspace_revalidated`, `staging_approval_checked`,
`rollback_plan_verified`, `staging_workspace_created`, `staged_changes_created`,
`regression_tests_recorded`, `stable_files_untouched`, `active_candidate_untouched`,
`safety_promotion_untouched`, `not_stable_promoted`, `no_secret_in_staging_artifacts`.

## Remaining risks / limits

- **No stable promotion yet** — that is a separate, human-driven, policy-gated phase.
- **staged changes still require human review** before any stable promotion.
- **Rollback verification must be confirmed** before stable promotion (here it is
  recorded; a stable phase needs a stronger, deployed-state rollback).
- **Full regression required before stable** — the fixed allowlist must pass.
- **Promotion policy must still be followed** for any stable move.
- **No real API.** Fake provider only.
- **Deterministic fake repair pipeline** — staged changes are templates, not real
  model-generated diffs.

## Next phase (not started)

**Stable promotion** — a human reviews the staging workspace + stable-promotion
checklist, confirms the verified rollback and full regression, completes the human
shell-execution review, and only then does the promotion policy move a candidate to
`stable`. Stable promotion must never touch stable automatically and must keep a
verified rollback.
