# Candidate Summary — open_localhost_browser_v1

## What failed before

The stable `open_localhost_browser` is a placeholder: it returns a fabricated
`{status: opened, dom_summary: "..."}` and never connects to anything. It cannot
consume the live server now produced by `start_local_server` keep_alive.

## What changed

A real localhost page-loader that consumes a kept-alive `server_url` (no stable
skill / safety gate / promotion policy changed):

- Resolves the URL: explicit `server_url` > `server_session_path`'s server_url >
  (orchestrator-supplied blackboard server_url, which arrives as `server_url`).
- Rejects non-localhost URLs with `url_not_allowed` before loading.
- Loads via a **layered engine**: Playwright (real browser, auto-used when
  installed) → HTTP fallback (`urllib` + `html.parser`). If no engine is usable
  (Playwright absent and `allow_http_fallback=False`), fails gracefully with
  `browser_runtime_missing` — never crashes the eval.
- Builds `page_snapshot.json` (title, visible_text_preview, links/buttons/forms
  + counts) and `result.json`; optional `screenshot.png` (Playwright only).
- Always closes its browser resources (`browser_closed: true`) and never starts
  or kills the server.

In-candidate fixture `fixtures/html_page_server` (title + link + button + form)
backs the e2e.

### Harness wiring (infrastructure, not stable skill manifest/safety/promotion)

- `src/orchestrator/orchestrator.py`:
  - `_build_inputs(open_localhost_browser)` passes `server_url`,
    `server_session_path` (from the start_local_server session), `timeout_sec`,
    and `screenshot` (the stable placeholder ignores the extras).
  - `browser_opened_localhost` evidence now accepts `status in (opened, loaded)`
    so the real candidate's `loaded` satisfies the vite slice.
  - new evidence rules: `server_started`, `browser_page_loaded`,
    `page_snapshot_created`, `result_json_created`, `no_lingering_server_process`.
- `evals/cli_browser_integration/vite_login_bug.yaml`: add `keep_alive: true` so
  the now-real browser candidate can load the live server (the orchestrator tears
  it down at run end). The slice stays at 1.0.
- `evals/browser/open_localhost_keep_alive_smoke.yaml`: new end-to-end eval
  (start_local_server keep_alive → open_localhost_browser → run-end teardown).

> Did **not** touch `start_local_server_v1.2` or `patch_file_and_run_tests_v2`.
> The only cross-candidate dependency is consuming start_local_server's
> `server_session`/`server_url` via the blackboard — no edits to that candidate.

## Tests added

`harnesses/candidates/open_localhost_browser_v1/tests/test_open_localhost_browser_v1.py`
(against an in-process threaded HTTP server):
- explicit localhost URL accepted (status loaded, 200, title)
- non-localhost URL rejected (`url_not_allowed`, nothing loaded)
- reads `server_url` from a `server_session.json`
- missing URL → `no_server_url`
- browser runtime missing → graceful `browser_runtime_missing` (monkeypatched
  `_playwright_available=False`, fallback disabled)
- `page_snapshot.json` created with all fields + correct link/button/form counts
- browser resources closed (`browser_closed`) and `result.json` written

`tests/unit/test_browser_keep_alive_e2e.py`:
- the browser keep-alive smoke eval scores 1.0 on all 5 criteria, and the
  orchestrator's finally teardown leaves no lingering server.

## Tests run

- `validate_structure` / `validate_workflows` — PASS
- `run_skill_tests` — 5/5 PASS
- `run_unit_tests` — **76/76 PASS** (68 prior + 7 browser + 1 e2e)
- `run_eval.py --task evals/browser/open_localhost_keep_alive_smoke.yaml` — 1.0
- `run_eval.py --task evals/patch_runner/py_calc_bug_e2e.yaml` — 1.0
- `run_demo.py --demo vite_login_bug` — 1.0
- No lingering `node`/`http.server` server or browser processes; `_sessions`
  registry empty after runs.

## Remaining risks

- **No real browser in this environment.** Playwright and browser binaries are
  not installed, so v1 runs the **HTTP fallback** engine: it loads the page and
  smoke-verifies it, but it is **not** a real browser — no JavaScript execution,
  no real DOM/rendering, no console, and no screenshot. A client-rendered SPA
  whose content is built by JS would snapshot as near-empty. Install `playwright`
  + a browser binary to use the real engine (the code path is wired and used
  automatically when present).
- **Graceful-fail vs e2e trade-off.** Because of the above, `browser_runtime_missing`
  is only returned when the fallback is explicitly disabled. The default loads via
  the fallback so the e2e can reach 1.0. This is a deliberate, documented choice.
- **`screenshot=true`** is honored only by the Playwright engine; the HTTP
  fallback returns `screenshot_ref=null`.
- **Snapshot is HTTP-level.** Links/buttons/forms come from the served HTML, not a
  rendered DOM; dynamic elements added by JS are not captured in fallback mode.
- **Orchestrator artifacts** for the browser step are written to a temp dir (the
  orchestrator does not pass `artifacts_dir`, to avoid `result.json` collisions
  with other skills); unit tests pass an explicit `artifacts_dir`.

## Promotion recommendation

Keep at `dev`. The real path executes a browser runtime, so promotion needs human
review (`promotion_policy.md`). Before a staging review: install Playwright + a
browser binary in the target environment and add a real-browser e2e (with JS
rendering + screenshot) so the fallback is not the only proven path.

## Files

New (candidate): `candidate.yaml`, `SKILL.md`, `candidate_summary.md`,
`scripts/open_localhost_browser.py`,
`fixtures/html_page_server/{package.json,server.js}`,
`tests/test_open_localhost_browser_v1.py`.

New (e2e): `evals/browser/open_localhost_keep_alive_smoke.yaml`,
`tests/unit/test_browser_keep_alive_e2e.py`.

Changed (harness infrastructure only): `src/orchestrator/orchestrator.py`
(browser inputs + evidence rules), `evals/cli_browser_integration/vite_login_bug.yaml`
(`keep_alive: true`).

Untouched (per constraints): stable `skills/` manifests, `safety_gate`,
`promotion_policy`, `read_browser_console`, `start_local_server_v1.2`, and
`patch_file_and_run_tests_v2`.
