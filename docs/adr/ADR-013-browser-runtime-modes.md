# ADR-013: Browser Runtime Modes (Playwright vs HTTP Fallback)

## Status

Accepted.

## Context

The `open_localhost_browser` candidate must consume a live localhost server and
verify that a page loads. A real browser (Playwright + a browser binary) gives
JavaScript execution, a rendered DOM, console access, and screenshots. But the
current sandbox has **no Playwright package and no browser binaries**, and
installing them needs network access and a large download.

We still want a useful, testable localhost smoke check in that environment, and
we want the `open_localhost_keep_alive_smoke` e2e to pass so the keep-alive
handoff is exercised end to end.

## Decision

`open_localhost_browser` supports two runtime **modes**, recorded on every
result:

- `browser_mode: playwright` — a real headless browser. Used automatically in
  `auto` mode when available. If the runtime is missing it fails cleanly with
  `failure_reason=browser_runtime_missing` (it never silently degrades).
- `browser_mode: http_fallback` — a pure-Python `urllib` + `html.parser` loader.
  It performs an HTTP GET of a localhost URL and extracts title / visible text /
  links / buttons / forms. It is a **smoke check, not a browser**: no JS, no
  rendered DOM, no console, no screenshot.

Every `result.json` carries explicit capability flags so a passing status can
never be mistaken for a real browser:

```
engine: playwright | http_fallback | null
is_real_browser: bool
screenshot_supported: bool
js_supported: bool
console_supported: bool
```

The orchestrator also copies `browser_engine` / `browser_is_real` into
`score.json` metrics.

We **allow** the HTTP fallback to back the localhost smoke e2e, because loading a
static localhost page and asserting it serves HTML is a legitimate (if shallow)
check and keeps the keep-alive handoff covered.

We **forbid** the HTTP fallback from backing any skill that needs real browser
semantics — first and foremost `read_browser_console`. A console skill built on
the fallback would report a fake/empty console (the fallback has no JS engine and
no console at all), which would silently corrupt every downstream design and
evaluation decision. Such skills MUST require `browser_mode: playwright` and fail
with `browser_runtime_missing` when it is absent.

## Consequences

- The localhost smoke e2e passes today via the fallback, with the result and
  score clearly marked `engine=http_fallback`, `is_real_browser=false`.
- `read_browser_console` (and any JS/console/screenshot-dependent capability) is
  blocked until a real Playwright environment is available — by policy, not by
  accident.
- Promotion of `open_localhost_browser` to `staging` requires a real-browser e2e
  (JS render + screenshot) per `playwright_verification_plan.md`; the fallback is
  not a sufficient promotion basis.
- When Playwright + a browser binary are installed, `auto` mode upgrades to the
  real browser with no code change.
