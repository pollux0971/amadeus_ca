# Open Localhost Browser — Candidate v1

## Status

`dev` candidate, `version: 1`, overrides the stable `open_localhost_browser`
placeholder when candidate overlays are enabled.

## What it does

Consumes a **live** `server_url` from a kept-alive `start_local_server`, opens
the page, builds a small page snapshot for smoke verification, and writes
artifacts. It does **not** start or tear down any server, and it never kills the
server process.

## Engine selection (most capable first)

1. **Playwright** (real headless browser) — used automatically when the
   `playwright` package and a browser binary are available.
2. **HTTP fallback** (`urllib` + `html.parser`) — loads and smoke-verifies the
   page without a real browser. No JS execution, no rendering, no screenshot.

If neither is usable (Playwright absent **and** `allow_http_fallback=False`), the
skill fails gracefully with `failure_reason=browser_runtime_missing` — it never
crashes the eval.

## Inputs

```yaml
server_url: string|null          # explicit URL (highest priority)
server_session_path: string|null # read server_url from this server_session.json
timeout_sec: integer             # default 15
screenshot: boolean              # default false (only honored by Playwright)
allow_http_fallback: boolean     # default true
artifacts_dir: string|null
```

### URL resolution priority

1. explicit `server_url`
2. `server_session_path`'s `server_url`
3. the orchestrator supplies the blackboard / previous-skill `server_url` as
   `server_url` (so tier 3 arrives through tier 1).

Only `http`/`https` URLs on `localhost` / `127.0.0.1` / `::1` are allowed; any
other URL is rejected with `failure_reason=url_not_allowed` before loading.

## Outputs (result.json)

```yaml
status: loaded | failed
url: string | null
title: string | null
status_code: integer | null
engine: playwright | http_fallback | null
browser_closed: boolean          # resources always closed
page_snapshot_ref / result_ref / screenshot_ref: string | null
failure_reason: string | null
```

## page_snapshot.json (on success)

```yaml
url: string
title: string | null
visible_text_preview: string     # first 300 chars
links:   [{href, text}]
buttons: [{text, type}]
forms:   [{action, method}]
counts:  {links, buttons, forms}
```

## Failure modes (all set `failure_reason`)

`no_server_url`, `url_not_allowed`, `browser_runtime_missing`, `page_load_failed`.

## Safety / lifecycle

- Never starts or kills a server (server lifecycle belongs to
  `start_local_server` + the orchestrator's end-of-run teardown).
- Every engine uses a context manager / explicit close, so no browser resource
  is left open; `browser_closed` reports this.
- Only localhost URLs are loaded.

## Out of scope (per task)

`read_browser_console`, scheduled reaper, real-browser screenshots in the HTTP
fallback.
