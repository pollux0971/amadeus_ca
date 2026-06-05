# Playwright Verification Plan — open_localhost_browser_v1 (staging gate)

This is the **staging gate** for `open_localhost_browser_v1`. The candidate must
pass a real-browser verification in a Playwright-enabled environment before it
can be considered for `staging`. The HTTP fallback path is **not** a sufficient
basis for promotion.

## Current state (why this gate exists)

- This sandbox has **no Playwright package and no browser binaries**
  (`import playwright` → ModuleNotFoundError; no `~/.cache/ms-playwright`).
- v1 therefore runs the **HTTP fallback** engine (`urllib` + `html.parser`). It
  loads a localhost URL and smoke-verifies the served HTML (title / text /
  links / buttons / forms), but it is **not a real browser**:
  - no JavaScript execution,
  - no rendered DOM (only the raw served HTML),
  - no browser console,
  - no screenshots.
- Every result is marked `engine=http_fallback`, `is_real_browser=false`,
  `js_supported=false`, `console_supported=false`, `screenshot_supported=false`,
  and the run's `score.json` records `browser_engine=http_fallback`.

## Consequence for downstream skills

- **`read_browser_console` must NOT be built on the HTTP fallback.** The fallback
  has no JS engine and no console; a console skill on top of it would emit a
  fake/empty console and pollute later design and evaluation decisions. Per
  ADR-013, `read_browser_console` requires `browser_mode: playwright` and must
  fail with `browser_runtime_missing` when Playwright is absent.

## What must pass before staging

Run in an environment with Playwright installed:

```bash
pip install playwright
playwright install chromium
```

1. **Real-browser smoke (browser_mode=playwright):**
   - Run `open_localhost_browser` against the keep-alive `html_page_server` with
     `browser_mode: playwright` and `screenshot: true`.
   - Assert `engine=playwright`, `is_real_browser=true`, `screenshot_supported=true`,
     `js_supported=true`, `console_supported=true`.
   - Assert `status=loaded`, `status_code=200`, a non-null `title`, and a written
     `screenshot.png`.
2. **JS-rendered content:** serve a page whose visible content is produced by
   JavaScript; assert the snapshot captures the rendered text (the fallback would
   miss it). This proves the real DOM path.
3. **Graceful fail still holds:** with Playwright uninstalled and
   `browser_mode: playwright`, assert `failure_reason=browser_runtime_missing`
   (no crash) — already covered by a unit test here.
4. **No lingering processes:** assert no browser or server process remains after
   the run (browser context/page closed; server torn down by the orchestrator).
5. **e2e at 1.0 on the real engine:** a `browser_mode: playwright` variant of
   `open_localhost_keep_alive_smoke` scores 1.0 with `browser_is_real=true`.

## Promotion decision

- [ ] Real-browser verification (items 1–5) passed in a Playwright environment.
- [ ] Human review of the browser runtime surface (ADR-013) signed off.

Until both boxes are checked, the candidate stays at `dev` and
`read_browser_console` is **blocked**.
