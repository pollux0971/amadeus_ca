# Demo script — Candidate Merge (v0, candidate-workspace-only)

A short, reproducible walk-through of the Phase 5 chain: **human-reviewed apply
workspace → candidate merge workspace → rollback plan → promotion review package →
no stable promotion**.

## Demo goal

Show that a *human-approved* apply workspace can be merged into a **candidate merge
workspace** — with **explicit human approval + a named reviewer, no active-candidate
change, no stable change, no promotion** — producing a rollback plan and a promotion
review package, and that merging without approval/reviewer is refused.

## Commands

```bash
# 1) Safe preview — validate + print the plan, create no workspace.
python scripts/repair_merge.py \
    --apply-workspace fixtures/repair/fake_approved_apply_workspace --dry-run

# 2) Merge into a candidate merge workspace (requires --approved + --reviewer).
python scripts/repair_merge.py \
    --apply-workspace fixtures/repair/fake_approved_apply_workspace \
    --approved --reviewer "operator" --merge-id fake_merge_smoke

# 3) Run the candidate-merge eval.
python scripts/run_eval.py --task evals/repair/fake_candidate_merge.yaml
```

## Expected output

1. **`repair_merge ... --dry-run`** → a `# Repair Merge Plan` block: merge
   validation `True`, reviewer `set`, the fixed test allowlist, then `[DRY-RUN] no
   merge workspace created, no target/active-candidate/stable modified, nothing
   promoted.` (exit 0).
2. **`repair_merge ... --approved --reviewer "operator"`** → `[WROTE] candidate
   merge workspace: …` and `[CANDIDATE-WORKSPACE-ONLY] stable untouched; active
   candidate untouched; nothing promoted; rollback plan + promotion review package
   included; …`. The workspace holds `merge_manifest.json`, `merged_changes/…`,
   `merge_report.md`, `rollback_plan.md`, `promotion_review_package.md`,
   `test_results.json`, `README.md`. Running **without** `--approved` or with an
   empty/placeholder `--reviewer` instead prints `[REJECTED] …` and exits **3**.
3. **`run_eval ... fake_candidate_merge`** → `[PASS] fake_candidate_merge
   score=1.0` with all 11 criteria met (`apply_workspace_revalidated`,
   `merge_approval_checked`, `merge_workspace_created`, `merged_changes_created`,
   `rollback_plan_created`, `promotion_review_package_created`,
   `targeted_tests_recorded`, `stable_files_untouched`,
   `safety_promotion_untouched`, `not_promoted`, `no_secret_in_merge_artifacts`).
   `score.json` records `merged_to_candidate_workspace_only: true`,
   `stable_modified: false`, `promoted: false`.

## How to explain it

- **Explicit approval + reviewer.** Merge needs *both* the human merge-approval
  marker `APPROVED_FOR_CANDIDATE_MERGE: true` with a named `Reviewer:` in the apply
  workspace's `merge_approval_checklist.md`, AND the operator's `--approved` flag
  with a non-empty `--reviewer`. Miss any and merge fails closed.
- **Candidate-workspace-only merge.** The approved changes are copied only into a
  fresh candidate merge workspace's `merged_changes/`. The live repo, **active
  candidates**, and stable are never written.
- **merged_changes.** Each proposed file from the apply workspace is copied into the
  merge workspace — a human reviews exactly what would land in a candidate, in one
  place.
- **Rollback plan.** Because nothing live was touched, `rollback_plan.md` documents
  that rolling back is simply deleting the merge workspace — fully reversible. A
  future promotion phase must define its own, stronger rollback.
- **Promotion review package.** `promotion_review_package.md` is a human checklist +
  summary (merged files, tests, rollback, source, reviewer) — input to a future
  staging/stable decision, not the decision itself.
- **No active candidate modification.** The merge lands in `_repair_merges/<id>/`,
  not in any existing/active candidate's runtime code.
- **No stable promotion.** Nothing is promoted to `staging` or `stable`; the
  promotion policy remains the gate for that, in a separate human-driven phase.

## Safety notes

- Default is dry-run; `--approved` + a non-empty `--reviewer` are required to create
  anything.
- Test commands are a FIXED allowlist (never apply-derived), recorded by default and
  run only on `--run-tests`; no raw shell.
- All merge artifacts are redacted; no secret reaches the workspace.
- Generated merge workspaces are gitignored; this demo touches no stable skill,
  active candidate, `safety_gate`, or `promotion_policy`.
