# Phase 5 — Candidate Merge v0 (Candidate Workspace Only)

This phase adds the next safe step after an apply workspace is **human-approved for
merge**: it merges the proposed changes into a **new candidate merge workspace**,
with a rollback plan and a promotion review package. It still does **not** modify
stable, an active candidate, or any real target file, and it does **not** promote.
It builds on Phase 4 (approved patch application).

## Why merge still cannot touch stable (or an active candidate)

Merging is one step closer to "real" change, so v0 keeps the same hard boundary and
adds only the *candidate-workspace* materialization:

- A human must approve merge (marker + named reviewer) **and** pass `--approved`
  with a non-empty `--reviewer`; otherwise merge is refused.
- The merge lands only in a fresh candidate merge workspace (`merged_changes/`);
  the live repo, active candidates, and stable are never written.
- A `rollback_plan.md` and a `promotion_review_package.md` are produced so a human
  can decide — and undo — safely.
- Nothing is promoted; stable, the safety gate, and the promotion policy are
  untouched.

This gives a human one place to review the merged candidate, the test record, the
rollback, and the promotion package before any staging/stable decision — without
the system ever editing the live tree.

## How a candidate merge workspace is built from an approved apply workspace

```
approved apply workspace (merge_approval_checklist.md: APPROVED_FOR_CANDIDATE_MERGE + Reviewer)
  → apply manifest re-validation   (workspace-only / not promoted / not stable-modified)
  → merge validation               (validate_merge: marker + reviewer + targets + secret)
  → create candidate merge workspace
        merged_changes/ + merge_manifest.json + merge_report.md +
        rollback_plan.md + promotion_review_package.md + test_results.json
  → record targeted tests + regression  (fixed allowlist; executed only on --run-tests)
  → staging / stable promotion     NOT in v0
```

Run it:

```bash
# safe preview — validate, print the plan, create no workspace
python scripts/repair_merge.py \
    --apply-workspace fixtures/repair/fake_approved_apply_workspace --dry-run

# merge into a candidate merge workspace (requires --approved + --reviewer)
python scripts/repair_merge.py \
    --apply-workspace fixtures/repair/fake_approved_apply_workspace \
    --approved --reviewer "operator" --merge-id fake_merge_smoke

python scripts/run_eval.py --task evals/repair/fake_candidate_merge.yaml   # → 1.0
```

## Targeted tests / regression

The merge records a **fixed, hardcoded** test allowlist (never derived from the
apply workspace): targeted (`validate_structure`, `validate_workflows`,
`run_unit_tests`) + regression (`vite_login_bug` demo,
`fake_approved_patch_application` eval, `fake_repair_proposal_only` eval). They are
recorded in `test_results.json` by default and executed only on `--run-tests`. This
is how a merge ties itself to the existing gates without running an arbitrary command.

## Rollback plan

Because no live file is touched, rollback is trivial and fully reversible:
**delete the merge workspace directory** — nothing else changes. The
`rollback_plan.md` records this, and notes that a future staging/stable promotion
phase must define its own, stronger rollback before changing any active/stable
artifact.

## Results

| Eval / check | Result |
|---|---|
| `fake_candidate_merge` (category `candidate_merge`) | **1.0** |
| `fake_approved_patch_application` (Phase 4) | **1.0** (still) |
| `fake_repair_proposal_only` (Phase 3) | **1.0** (still) |
| `fake_full_browser_plan_execution` (planner execution) | **1.0** (still, real browser) |
| `run_full_browser_gate.py --dry-run` | **safe** |
| `repair_merge.py` without `--approved` / empty `--reviewer` | **rejected** (exit 3) |
| stable files modified | **none** |
| promoted | **false** (no auto promotion) |
| secret in merge artifacts | **none** (all redacted) |

Success criteria met: `apply_workspace_revalidated`, `merge_approval_checked`,
`merge_workspace_created`, `merged_changes_created`, `rollback_plan_created`,
`promotion_review_package_created`, `targeted_tests_recorded`,
`stable_files_untouched`, `safety_promotion_untouched`, `not_promoted`,
`no_secret_in_merge_artifacts`.

## Remaining risks / limits

- **No staging/stable promotion yet** — that is a separate, human-driven phase.
- **proposed/merged changes still require human review** before any promotion.
- **Targeted regression required before promotion** — the fixed allowlist must pass.
- **Rollback is workspace-deletion only** — a future promotion phase needs a
  stronger, deployed-state rollback.
- **No real API.** Fake provider only.
- **Deterministic fake repair pipeline** — proposals/merges are templates, not
  real model-generated diffs.

## Next phase (not started)

**Staging / stable promotion** — a human reviews the candidate merge workspace +
promotion review package, runs the regression gates, confirms the rollback, and
only then does the promotion policy move a candidate toward `staging`/`stable`.
Promotion must never touch stable, the safety gate, or the promotion policy
automatically, and must keep a rollback.
