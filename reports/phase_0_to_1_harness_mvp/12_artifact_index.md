# 12 · Artifact Index

Key files for this phase (paths relative to the repo root).

## Entry points / status

- `README.md` — repo entry; "Current Harness Candidate Status" + "Gate Chain".
- `docs/quick_resume.md` — one-minute "where am I" resume note.
- `docs/candidate_status_matrix.md` — per-candidate status table.
- `docs/promotion_readiness_review.md` — per-candidate promotion verdicts.
- `docs/next_milestone_plan.md` — ordered next steps.
- `docs/checkpoints/checkpoint-0-to-1-harness-gates.md` — frozen checkpoint /
  handoff note (tag: `checkpoint-0-to-1-harness-gates`).

## Gates (scaffolded; do not run for real yet)

- `scripts/run_playwright_gate.py` — Playwright real-browser gate runner.
- `scripts/run_full_browser_gate.py` — full browser e2e gate runner.
- `evals/browser/open_localhost_playwright_required_smoke.yaml` — real-browser gate eval.
- `evals/browser/full_browser_vite_login_bug_e2e.yaml` — full browser e2e (draft/blocked).

## Decision record

- `docs/adr/ADR-013-browser-runtime-modes.md` — Playwright vs HTTP fallback; why
  the fallback may back a smoke but must not back the console skill.

## Candidates (all under `harnesses/candidates/`)

- `patch_file_and_run_tests_v1/` (superseded), `patch_file_and_run_tests_v2/`
- `start_local_server_v1/` (release 1.2; keep_alive + teardown + lease reaper)
  - `scripts/reap_server_sessions.py` — manual lease reaper CLI.
- `open_localhost_browser_v1/` + `playwright_verification_plan.md`

## Evals / fixtures used in demos

- `evals/walking_skeleton/inspect_only.yaml`
- `evals/cli_browser_integration/vite_login_bug.yaml`
- `evals/patch_runner/py_calc_bug_e2e.yaml`
- `evals/server/keep_alive_smoke.yaml`
- `evals/browser/open_localhost_keep_alive_smoke.yaml`

## This report pack

- `reports/phase_0_to_1_harness_mvp/` — this folder (README + `01`–`12`).
