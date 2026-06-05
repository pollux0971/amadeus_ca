# Candidate Summary — open_localhost_browser_v1

> **Status: dev. NOT recommended for staging** until a real-browser (Playwright)
> e2e passes — see `playwright_verification_plan.md` and ADR-013. The e2e is 1.0
> today only via the **HTTP fallback** (`engine=http_fallback`,
> `is_real_browser=false`). **`read_browser_console` is blocked** until the real
> Playwright browser mode is available (a console on the fallback would be fake).

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

### Browser runtime modes + capability flags (ADR-013)

`browser_mode` makes the runtime explicit: `auto` (Playwright → fallback),
`playwright` (real browser only; missing → `browser_runtime_missing`),
`http_fallback` (forced degraded loader). Every `result.json` now carries
capability flags so a passing status can never be mistaken for a real browser:
`engine`, `is_real_browser`, `screenshot_supported`, `js_supported`,
`console_supported`. The orchestrator also copies `browser_engine` /
`browser_is_real` into `score.json` metrics. See
`playwright_verification_plan.md` for the staging gate and ADR-013 for why the
fallback may back the localhost smoke but must NOT back `read_browser_console`.

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
- **http_fallback engine + capability flags** — `engine=http_fallback`,
  `is_real_browser/js/console/screenshot_supported=false`, persisted to result.json
- **playwright mode graceful fail** — `browser_mode=playwright` with no runtime →
  `browser_runtime_missing`, `engine=null`, `is_real_browser=false`

`tests/unit/test_browser_keep_alive_e2e.py`:
- the browser keep-alive smoke eval scores 1.0 on all 5 criteria, the
  orchestrator's finally teardown leaves no lingering server, and the score
  metrics record `browser_engine=http_fallback` / `browser_is_real=false`.

## Tests run

- `validate_structure` / `validate_workflows` — PASS
- `run_skill_tests` — 5/5 PASS
- `run_unit_tests` — **78/78 PASS** (76 prior + 2 runtime-mode)
- `run_eval.py --task evals/browser/open_localhost_keep_alive_smoke.yaml` — 1.0
  (score metrics: `browser_engine=http_fallback`, `browser_is_real=false`)
- `run_eval.py --task evals/patch_runner/py_calc_bug_e2e.yaml` — 1.0
- `run_demo.py --demo vite_login_bug` — 1.0
- No lingering `node`/`http.server` server or browser processes; `_sessions`
  registry empty after runs.

## Remaining risks

- **[#1] Not a real browser path in this environment.** Playwright and browser
  binaries are not installed, so v1 runs the **HTTP fallback** engine: it loads
  the page and smoke-verifies it, but it is **not** a real browser — no
  JavaScript execution, no real DOM/rendering, no console, and no screenshot. A
  client-rendered SPA whose content is built by JS would snapshot as near-empty.
  Results are explicitly marked `engine=http_fallback`, `is_real_browser=false`.
  This remains the **#1 risk** until the Playwright verification (ADR-013,
  `playwright_verification_plan.md`) passes. **`read_browser_console` is blocked
  until then** — a console built on the fallback would be fake/empty.
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

Keep at `dev`. **Not recommended for `staging`** until the real-browser
(Playwright) verification in `playwright_verification_plan.md` passes — the
current 1.0 rests on the HTTP fallback, which is not a real browser. The real
path executes a browser runtime, so promotion also needs human review
(`promotion_policy.md`). `read_browser_console` must wait for the real Playwright
browser mode (ADR-013).

## Files

New (candidate): `candidate.yaml`, `SKILL.md`, `candidate_summary.md`,
`playwright_verification_plan.md`, `scripts/open_localhost_browser.py`,
`fixtures/html_page_server/{package.json,server.js}`,
`tests/test_open_localhost_browser_v1.py`.

New (docs): `docs/adr/ADR-013-browser-runtime-modes.md`.

New (e2e): `evals/browser/open_localhost_keep_alive_smoke.yaml`,
`tests/unit/test_browser_keep_alive_e2e.py`.

Changed (harness infrastructure only): `src/orchestrator/orchestrator.py`
(browser inputs incl. `browser_mode`; evidence rules; `browser_engine` /
`browser_is_real` in score metrics), `evals/cli_browser_integration/vite_login_bug.yaml`
(`keep_alive: true`).

Untouched (per constraints): stable `skills/` manifests, `safety_gate`,
`promotion_policy`, `read_browser_console`, `start_local_server_v1.2`, and
`patch_file_and_run_tests_v2`.
