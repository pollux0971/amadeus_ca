# Candidate Summary — read_browser_console_v1

> **Status: dev.** Real Playwright console collector. **No http_fallback, no fake
> console.** Stays `dev` until the console smoke eval is confirmed (it is — 1.0 in
> a Playwright env); promotion to staging needs human review. This round does the
> console smoke only — **full_browser_vite_login_bug_e2e is still blocked**.

## What failed before

The stable `read_browser_console` is a placeholder (`summarize_console`) that just
counts whatever message list it is handed — it never opens a browser and has no
real console.

## What changed

A real **Playwright-only** console collector:

- Forces a real browser: `browser_mode` defaults to `playwright`;
  `http_fallback` → `http_fallback_not_allowed`; missing runtime →
  `browser_runtime_missing`. **Never fabricates a console.**
- Resolves the URL (server_url > server_session_path > orchestrator blackboard),
  localhost-only (`url_not_allowed` otherwise).
- Listens to `page.on("console")` and `page.on("pageerror")` on a live localhost
  page; classifies entries into fatal / error / warning / info / debug; `pageerror`
  → fatal.
- Writes `console_log.json` + `result.json` (+ optional page_snapshot / screenshot).
- Closes its browser resources (`browser_closed=true`) and **never starts or kills
  the server** (lifecycle stays with start_local_server + the orchestrator).
- Emits back-compat `console_errors` / `fatal_error_count` so existing evals that
  only check those keys keep working.

In-candidate fixture `fixtures/console_smoke_page` emits log/info/warn/error.

### Harness wiring (infrastructure; not stable skill/safety/promotion)

- `src/orchestrator/orchestrator.py`: `_build_inputs(read_browser_console)` passes
  server_url / server_session_path / browser_mode / timeout / wait / fail-on-error
  / screenshot (and keeps `messages` for the stable placeholder). New evidence
  rules: `real_browser_page_loaded`, `console_collected`, `console_log_created`,
  `console_supported_true`, `engine_playwright`; `result_json_created` and
  `no_lingering_server_process` generalized to also cover the console step.
- `evals/browser/read_browser_console_smoke.yaml`: the console smoke (real
  browser; `require_real_browser: true`).

## Results

- **read_browser_console_smoke → 1.0** in a Playwright env (`.venv`): all 8
  criteria including `console_collected`, `console_supported_true`,
  `engine_playwright`. console_log.json counts `{error:1, warning:1, info:1,
  debug:1, fatal:0}` for the smoke page.
- `open_localhost_playwright_required_smoke` 1.0; existing `vite_login_bug`,
  `open_localhost_keep_alive_smoke`, `py_calc_bug_e2e` still 1.0 (the console
  candidate graceful-fails under no-Playwright runs without breaking them).
- No lingering server/browser processes.

## Remaining risks

- **Requires a real Playwright runtime.** Under no-Playwright interpreters the
  step fails with `browser_runtime_missing` (by design — no fake console). The
  real path is verified via the project `.venv`.
- The console smoke uses a clean page (no uncaught error). `pageerror`/fatal
  capture is exercised by unit tests against a throwing page.
- Executes a browser runtime → promotion needs human review.

## Promotion recommendation

Keep at `dev`. Next: wire it into `full_browser_vite_login_bug_e2e` (still
blocked / not this round) and run `scripts/run_full_browser_gate.py` only once
that chain is ready.

## Files

New (candidate): `candidate.yaml`, `SKILL.md`, `candidate_summary.md`,
`scripts/read_browser_console.py`, `fixtures/console_smoke_page/{package.json,server.js}`,
`tests/test_read_browser_console_v1.py`.
New (eval): `evals/browser/read_browser_console_smoke.yaml`.
Changed (harness infra only): `src/orchestrator/orchestrator.py` (inputs +
evidence rules). Untouched: stable skills, safety_gate, promotion_policy,
patch_file_and_run_tests_v2, start_local_server_v1.2, open_localhost_browser_v1
runtime code.
