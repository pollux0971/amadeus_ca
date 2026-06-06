# Phase 1B — Full Real-Browser E2E Gate PASSED

The full real-browser end-to-end gate is **wired and passing**.
`full_browser_vite_login_bug_e2e` is now an **executable gate** (no longer a
draft) and scores **1.0** via `scripts/run_full_browser_gate.py` in a Playwright
+ Chromium environment.

## Result

- **timestamp:** 2026-06-06T02:15:24Z
- **gate:** `python scripts/run_full_browser_gate.py` → **exit 0 (PASS)**
  (all prerequisites met: playwright package, chromium runtime,
  `open_localhost_browser_v1` staging-ready, `read_browser_console` candidate).
- **eval:** `full_browser_vite_login_bug_e2e` → **score = 1.0** (all 8 criteria).
- **engine = playwright**, **is_real_browser = true** (real Chromium).

## Chain (steps in order)

```
start_local_server (keep_alive)
  → open_localhost_browser  (as open_pre,  real browser)
  → read_browser_console    (as console_pre)
  → patch_file_and_run_tests
  → open_localhost_browser  (as open_post, real browser RE-OPEN)
  → read_browser_console    (as console_post)
  → orchestrator finally: teardown the kept-alive server
```

Aliased `as: open_pre/console_pre/open_post/console_post` steps let the same
skills run pre- and post-patch (minimal orchestrator support — no DAG, no planner).

## Criteria (all pass)

`server_started`, `real_browser_page_loaded`, `console_error_collected`,
`patch_applied`, `tests_pass`, `browser_reverify_passed`,
`no_fatal_console_error_after_patch`, `no_lingering_server_process`.

## Console counts

- **pre-patch** (`console_pre`): `{error: 1, warning: 1, info: 0, debug: 1, fatal: 0, total: 3}`
  → a real console error was collected (`console_error_collected`).
- **post-patch** (`console_post`): `{error: 1, warning: 1, info: 0, debug: 1, fatal: 0, total: 3}`
  → **fatal = 0** after the patch (`no_fatal_console_error_after_patch`). The page
  loads with no uncaught/fatal error; the source bug fix is verified by
  `tests_pass` (the served console.error is a non-fatal symptom, by fixture design).

## Artifacts (this run; ephemeral temp dirs are NOT committed)

- `runs/full_browser_vite_login_bug_e2e_*/`: `score.json`, `trace.jsonl`,
  `summary.md`, `task.yaml`, and `artifacts/patch.diff` + `artifacts/test.log`
  (from patch_file_and_run_tests_v2).
- console: `console_log.json` + `result.json` per console step (temp
  `console_artifacts_*`).
- browser: `result.json` + `page_snapshot.json` per open step (temp
  `browser_artifacts_*`).

## No lingering process

Precise check (`ms-playwright|headless_shell|chrome-linux64/chrome|node server.js|http.server`):
**none** ✅ (the operator's pre-existing desktop Chrome is unrelated/untouched).

## Fixture

Dedicated `fixtures/vite_login_bug_browser/` (node page logging a console error +
`login.py`/`test_login.py` for the patch). The original `fixtures/vite_login_bug/`
is **not polluted**.

## Invariants

- stable skills / safety_gate / promotion_policy **untouched**.
- patch_file_and_run_tests_v2 / start_local_server_v1.2 / open_localhost_browser_v1
  runtime code **unchanged**; read_browser_console_v1 still forces
  `browser_mode=playwright` (no http_fallback).
- `open_localhost_browser_v1` stays **staging-ready**.
- No `.venv` / browser cache / runs / screenshots / secrets committed.

## Verification (existing suite, system interpreter)

- `validate_structure` / `validate_workflows` PASS; `run_skill_tests` 5/5;
  `run_unit_tests` all pass (Playwright-only tests skip under system).
- `read_browser_console_smoke`, `open_localhost_playwright_required_smoke` 1.0
  (venv); `open_localhost_keep_alive_smoke`, `py_calc_bug_e2e`, `vite_login_bug`
  1.0 (system).
