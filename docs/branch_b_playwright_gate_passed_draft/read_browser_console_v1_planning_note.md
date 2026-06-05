# read_browser_console_v1 — Planning Note (NOT an implementation)

> This is a **planning note only**. No candidate exists; nothing here is built or
> activated. Do not start `read_browser_console` until the Playwright gate has
> passed and Branch B is applied.

## Minimum requirements (future v1)

a. **Must require `browser_mode=playwright`.** The console is meaningful only on a
   real browser.

b. **Missing Playwright → `failure_reason=browser_runtime_missing`** (graceful
   fail, never crash). No silent degrade.

c. **http_fallback is forbidden / not allowed for the console.** The HTTP fallback
   has no JS engine and no console; building a console on it would be fake. The
   skill must refuse the fallback engine entirely (per ADR-013).

d. **Collect console logs from the Playwright page/context** (e.g. the page
   `console` events and page errors).

e. **Produce `console_log.json`** — the captured console entries.

f. **Produce `result.json`** — status (`collected | failed`), counts, refs,
   `failure_reason`, and the runtime capability flags (`engine=playwright`,
   `is_real_browser=true`, `console_supported=true`).

g. **Classify entries** into `fatal` / `error` / `warn` / `info`, with a
   `fatal_error_count` for evaluation.

h. **Must not start or kill the server** — server lifecycle stays with
   `start_local_server` + the orchestrator's end-of-run teardown.

i. **Close browser resources properly** (context/page closed; no lingering browser
   process), mirroring `open_localhost_browser_v1`.

j. **Build a console smoke eval first** (real browser, asserts
   `console_supported=true` + a captured/classified entry) **before** wiring it
   into `full_browser_vite_login_bug_e2e`.

## Out of scope for this note

- No code, no `candidate.yaml`, no evidence rules, no eval execution.
- The full browser e2e stays blocked until this candidate exists.
