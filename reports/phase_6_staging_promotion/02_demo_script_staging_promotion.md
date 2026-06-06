# Demo script — Staging Promotion (v0, staging-workspace-only)

A short, reproducible walk-through of the Phase 6 chain: **human-reviewed candidate
merge workspace → staging promotion workspace → rollback verification → stable
promotion checklist → no stable promotion**.

## Demo goal

Show that a *human-approved* candidate merge workspace can be promoted into a
**staging workspace** — with **explicit human approval + a named reviewer, no
active-candidate change, no stable change, no stable promotion** — producing a
rollback verification and a stable-promotion checklist, and that promoting without
approval/reviewer is refused.

## Commands

```bash
# 1) Safe preview — validate + print the plan, create no workspace.
python scripts/staging_promote.py \
    --merge-workspace fixtures/repair/fake_approved_merge_workspace --dry-run

# 2) Promote into a staging workspace (requires --approved + --reviewer).
python scripts/staging_promote.py \
    --merge-workspace fixtures/repair/fake_approved_merge_workspace \
    --approved --reviewer "operator" --staging-id fake_staging_smoke

# 3) Run the staging-promotion eval.
python scripts/run_eval.py --task evals/repair/fake_staging_promotion.yaml
```

## Expected output

1. **`staging_promote ... --dry-run`** → a `# Staging Promotion Plan` block: staging
   validation `True`, reviewer `set`, rollback plan present `True`, the fixed test
   allowlist, then `[DRY-RUN] no staging workspace created, no
   target/active-candidate/stable modified, nothing stable-promoted.` (exit 0).
2. **`staging_promote ... --approved --reviewer "operator"`** → `[WROTE] staging
   promotion workspace: …` and `[STAGING-WORKSPACE-ONLY] stable untouched; active
   candidate untouched; nothing stable-promoted; rollback verification + stable
   promotion checklist included; …`. The workspace holds `staging_manifest.json`,
   `staged_changes/…`, `staging_report.md`, `rollback_verification.md`,
   `regression_results.json`, `stable_promotion_checklist.md`, `README.md`. Running
   **without** `--approved` or with an empty/placeholder `--reviewer` instead prints
   `[REJECTED] …` and exits **3**.
3. **`run_eval ... fake_staging_promotion`** → `[PASS] fake_staging_promotion
   score=1.0` with all 11 criteria met (`merge_workspace_revalidated`,
   `staging_approval_checked`, `rollback_plan_verified`, `staging_workspace_created`,
   `staged_changes_created`, `regression_tests_recorded`, `stable_files_untouched`,
   `active_candidate_untouched`, `safety_promotion_untouched`, `not_stable_promoted`,
   `no_secret_in_staging_artifacts`). `score.json` records
   `staged_to_workspace_only: true`, `stable_modified: false`, `stable_promoted:
   false`, `active_candidate_modified: false`.

## How to explain it

- **Explicit approval + reviewer.** Staging needs *both* the human
  staging-approval marker `APPROVED_FOR_STAGING_PROMOTION: true` with a named
  `Reviewer:` in the merge workspace's `staging_approval_checklist.md`, AND the
  operator's `--approved` flag with a non-empty `--reviewer`. Miss any and staging
  fails closed.
- **Staging-workspace-only.** The approved changes are copied only into a fresh
  staging workspace's `staged_changes/`. The live repo, **active candidates**, and
  stable are never written.
- **staged_changes.** Each merged file from the candidate merge workspace is copied
  into the staging workspace — a human reviews exactly what would be staged, in one
  place.
- **Rollback verification.** `rollback_verification.md` confirms the source rollback
  plan is present and that rolling back staging is simply deleting the staging
  workspace — fully reversible. A future stable phase needs a stronger,
  deployed-state rollback.
- **Stable promotion checklist.** `stable_promotion_checklist.md` is a human checklist
  + summary (staged files, tests, rollback, source, reviewer) — input to a future
  stable decision, not the decision itself.
- **No active candidate modification.** Staging lands in `_staging_promotions/<id>/`,
  not in any existing/active candidate's runtime code.
- **No stable promotion.** Nothing is promoted to `stable`; the promotion policy
  remains the gate for that, in a separate human-driven phase.

## Safety notes

- Default is dry-run; `--approved` + a non-empty `--reviewer` are required to create
  anything.
- Test commands are a FIXED allowlist (never merge-derived), recorded by default and
  run only on `--run-tests`; no raw shell.
- All staging artifacts are redacted; no secret reaches the workspace.
- Generated staging workspaces are gitignored; this demo touches no stable skill,
  active candidate, `safety_gate`, or `promotion_policy`.
