# Demo script — Approved Patch Application (v0, workspace-only)

A short, reproducible walk-through of the Phase 4 chain: **human-approved proposal
→ workspace-only apply → proposed_changes → fixed test allowlist → apply report →
no merge / no promotion**.

## Demo goal

Show that an *approved* repair proposal can be materialized into an **apply
workspace** — with **explicit human approval, no stable change, no merge, and no
promotion** — and that applying without approval is refused.

## Commands

```bash
# 1) Safe preview — validate + print the plan, create no workspace.
python scripts/repair_apply.py \
    --proposal-workspace fixtures/repair/fake_approved_proposal_workspace --dry-run

# 2) Apply to a candidate apply workspace (requires explicit --approved).
python scripts/repair_apply.py \
    --proposal-workspace fixtures/repair/fake_approved_proposal_workspace \
    --approved --apply-id fake_apply_smoke

# 3) Run the workspace-only apply eval.
python scripts/run_eval.py --task evals/repair/fake_approved_patch_application.yaml
```

## Expected output

1. **`repair_apply ... --dry-run`** → a `# Repair Apply Plan` block: proposal
   revalidated `True`, approval marker `True` / reviewer `set`, apply validation
   `True`, the fixed test allowlist, the proposed actions, then `[DRY-RUN] no apply
   workspace created, no target modified, nothing promoted.` (exit 0).
2. **`repair_apply ... --approved`** → `[WROTE] apply workspace: …` and
   `[WORKSPACE-ONLY] stable untouched; nothing promoted; human review still
   required for merge/promotion.` The workspace holds `apply_manifest.json`,
   `proposed_changes/…`, `apply_report.md`, `test_results.json`, `README.md`.
   Running it **without** `--approved` instead prints `[REJECTED] … requires
   explicit --approved …` and exits **3**.
3. **`run_eval ... fake_approved_patch_application`** → `[PASS]
   fake_approved_patch_application score=1.0` with all 9 criteria met
   (`proposal_revalidated`, `approval_marker_checked`, `apply_workspace_created`,
   `proposed_changes_created`, `targeted_tests_recorded`, `stable_files_untouched`,
   `safety_promotion_untouched`, `not_promoted`, `no_secret_in_apply_artifacts`).
   `score.json` records `applied_to_workspace_only: true`, `stable_modified:
   false`, `promoted: false`.

## How to explain it

- **Explicit approval.** Apply needs *two* signals: the human approval marker
  `APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY: true` plus a named `Reviewer:` in the
  proposal's `approval_checklist.md`, AND the operator's `--approved` flag on the
  command. Miss either and apply fails closed — there is no way to apply by
  accident.
- **Workspace-only apply.** The approved change is materialized only under the
  apply workspace's `proposed_changes/`. The intended target files in the repo are
  never written or overwritten, so the live tree is unchanged.
- **proposed_changes.** Each non-noop action becomes one *proposed* file (a
  redacted change note) inside the workspace — a human reviews exactly what would
  be applied, in one place, before deciding to merge.
- **Fixed test allowlist.** The only commands apply can run are a hardcoded
  constant (`validate_structure`, `validate_workflows`, `run_unit_tests`, the
  `vite_login_bug` demo) — never derived from the proposal and never a shell. They
  are recorded by default and executed only on `--run-tests`.
- **No merge / no promotion.** The apply workspace is never merged into the repo
  and nothing is promoted. `apply_manifest.json` records `promoted: false`,
  `stable_modified: false`. Merge and promotion are a separate, human-driven phase.
- **Stable untouched.** No action may target a stable skill, the safety gate, or
  the promotion policy; the apply validator rejects such targets. The whole phase
  leaves stable / safety_gate / promotion_policy unchanged.

## Safety notes

- Default is dry-run; `--approved` is required to create anything.
- All apply artifacts are redacted; no secret reaches the workspace.
- Generated apply workspaces are gitignored; this demo touches no stable skill,
  `safety_gate`, or `promotion_policy`.
