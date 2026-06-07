# 01 — Current State

Snapshot of the repo as audited (read from redacted docs/checkpoints/reports). Audit
only — nothing changed.

## Latest checkpoint

- **`checkpoint-phase-6-staging-promotion`** (tag) — staging promotion v0, frozen.
  Earlier: `checkpoint-phase-5-candidate-merge`, `checkpoint-phase-4-approved-patch-
  application`, `checkpoint-phase-3-repair-proposal-only`,
  `checkpoint-phase-2a-fake-planner-execution`, `checkpoint-phase-1b-full-browser-e2e`,
  `checkpoint-0-to-1-harness-gates`.

## Phase 1B → Phase 6 status

| Phase | State | Evidence |
|---|---|---|
| 1B full real-browser e2e | complete | `checkpoint-phase-1b-full-browser-e2e`; `full_browser_vite_login_bug_e2e` 1.0 (.venv) |
| 2A fake planner execution bridge | complete | `checkpoint-phase-2a-fake-planner-execution`; `fake_full_browser_plan_execution` 1.0 (.venv) |
| 3 repair proposal-only | complete | `checkpoint-phase-3-repair-proposal-only`; `fake_repair_proposal_only` 1.0 |
| 4 approved patch application (workspace-only) | complete | `checkpoint-phase-4-approved-patch-application`; `fake_approved_patch_application` 1.0 |
| 5 candidate merge (workspace-only) | complete | `checkpoint-phase-5-candidate-merge`; `fake_candidate_merge` 1.0 |
| 6 staging promotion (workspace-only) | complete | `checkpoint-phase-6-staging-promotion`; `fake_staging_promotion` 1.0 |

## Dashboard / demo package

- **UI dashboard:** read-only skeleton + snapshot generator + validator; real-browser
  smoke gate `ui_dashboard_readonly_smoke` 1.0 (.venv). No action surface.
- **Demo package:** `demo_package/` single-entry showcase complete (safe commands only).

## Provider / API

- **Fake provider only.** `llm_smoke --fake-only` → fake; loader fails closed; real
  providers are planning-only. **No real API call.** No `.env` key value read; no
  `/data/python/computer_agent_v5/password_and_api.txt` read.

## Invariants (verified untouched)

- **stable skills** untouched · **active candidate runtime** untouched ·
  **safety_gate** untouched · **promotion_policy** untouched.
- Secret hygiene green; all artifacts redacted; generated workspaces/snapshots/runs
  gitignored (not committed).

## Candidate stages (from `docs/candidate_status_matrix.md`)

- `patch_file_and_run_tests_v2` — staging-ready (needs human shell review before stable).
- `open_localhost_browser_v1` — staging-ready (real-browser gate passed).
- `start_local_server_v1.2` — dev. `read_browser_console_v1` — dev.
- Repair chain: AutoRepairLoop v0 / ApprovedPatchApplication v0 / CandidateMerge v0 /
  StagingPromotion v0 — all **workspace-only completed**; **StablePromotion — not
  started / blocked**.
