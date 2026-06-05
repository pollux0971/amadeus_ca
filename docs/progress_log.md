# Progress Log

Chronological log of where the project stands. For a one-minute resume see
[`quick_resume.md`](quick_resume.md); for the frozen snapshot see
[`checkpoints/checkpoint-0-to-1-harness-gates.md`](checkpoints/checkpoint-0-to-1-harness-gates.md).

## Current state (verified)

- **Git:** `main` synced with `origin/main`; working tree clean; 19 commits;
  tag `checkpoint-0-to-1-harness-gates` on local + remote. Repo:
  `https://github.com/pollux0971/amadeus_ca`.
- **Health:** `validate_structure` / `validate_workflows` PASS;
  `run_skill_tests` 5/5; `run_unit_tests` **113/113**.
- **Scores:** `vite_login_bug` 1.0, `py_calc_bug_e2e` 1.0,
  `open_localhost_keep_alive_smoke` 1.0 (`browser_engine=http_fallback`).
- **Active overrides:** `open_localhost_browser → v1`,
  `patch_file_and_run_tests → v2`, `start_local_server → v1 (1.2)`.
- **Gate status:** Playwright real-browser gate **BLOCKED** (no Playwright here);
  full browser gate **draft/blocked**. No lingering processes.
- **Invariants:** stable skills / safety_gate / promotion_policy untouched the
  whole way.

## Timeline

| Stage | Outcome | Key commits |
|---|---|---|
| Walking skeleton | real eval→registry→skill→trace→score loop | `Wire the walking skeleton` |
| patch_file_and_run_tests v1 → v2 | demo-specific → plan-driven reusable; v1 superseded; non-vite e2e 1.0 | `Candidate v1`, `Candidate v2`, `Add non-vite end-to-end eval`, `Staging promotion prep` |
| start_local_server v1 → v1.1 → v1.2 | subprocess lifecycle → keep_alive/teardown → lease reaper | `start_local_server_v1`, `v1.1`, `v1.2` |
| open_localhost_browser_v1 | consumes keep-alive server; http_fallback smoke 1.0 | `consume the keep-alive server_url`, `Browser runtime gate` |
| Status / gates / docs | candidate matrix + Playwright gate + full-browser gate drafts + README index + checkpoint + phase report | `Candidate status review`, `Playwright gate scaffolding`, `Full real-browser e2e gate draft`, `README index`, `Checkpoint`, `Phase report pack` |
| Phase 1A | Playwright gate run → BLOCKED (no runtime); attempt recorded; no status change | `Phase 1A: Playwright real-browser gate attempt — BLOCKED` |
| Branch B drafts | ready-to-apply (inert) docs for after the gate passes | `Branch B ready-to-apply drafts` |

## Blocked / not done (by design)

- **open_localhost_browser_v1 stays `dev`** — http_fallback is not a real browser;
  needs the Playwright gate. (Branch B drafts ready to apply once it passes.)
- **read_browser_console blocked** — no candidate; must wait for a real browser.
- **Playwright / full browser gates not executed** — no Playwright/Chromium here.

## Next real step

In a Playwright + Chromium environment: `python scripts/run_playwright_gate.py`
(must score 1.0, `is_real_browser=true`). On PASS, apply Branch B per
[`branch_b_playwright_gate_passed_draft/branch_b_apply_checklist.md`](branch_b_playwright_gate_passed_draft/branch_b_apply_checklist.md),
then start `read_browser_console_v1` (forcing `browser_mode=playwright`).
