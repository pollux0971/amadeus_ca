# Read Browser Console — Candidate v1

## Status

`dev` candidate, `version: 1`, overrides the stable `read_browser_console`
placeholder when candidate overlays are enabled.

## What it does

Collects **real** browser console output (and uncaught page errors) from a live
localhost page using a real Playwright browser, classifies it, and writes
artifacts. It does **not** start or kill the server, and it **never** uses an
HTTP fallback or fabricates a console.

## Runtime policy (strict — no fake console)

- `browser_mode` defaults to `playwright`; a missing `browser_mode` is treated as
  `playwright`.
- `browser_mode == "http_fallback"` → `failure_reason=http_fallback_not_allowed`.
- Playwright package / browser runtime missing → `failure_reason=browser_runtime_missing`.
- No fallback console is ever produced.

## Inputs

```yaml
server_url: string|null
server_session_path: string|null   # read server_url from this server_session.json
browser_mode: string               # default "playwright"; "http_fallback" is rejected
timeout_sec: integer               # default 15
wait_after_load_ms: integer        # default 300; settle time to capture console
fail_on_console_error: boolean     # default false
screenshot: boolean                # default false (Playwright only)
artifacts_dir: string|null
```

URL resolution: explicit `server_url` > `server_session_path`'s server_url >
(orchestrator-supplied blackboard server_url). Missing → `missing_server_url`.
Only `http/https` localhost/127.0.0.1/::1 URLs are allowed (else `url_not_allowed`).

## Outputs (result.json)

```yaml
status: collected | failed
engine: playwright              # on success
is_real_browser: true           # on success
console_supported: true         # on success
url, title, status_code
console_counts: {fatal, error, warning, info, debug, total}
has_fatal_console_error, has_console_error
console_errors: [...]           # back-compat (error entries)
fatal_error_count: integer      # back-compat (== console_counts.fatal)
console_log_ref / result_ref / page_snapshot_ref / screenshot_ref
browser_closed: true
failure_reason: string|null
```

## console_log.json

```yaml
url, title
entries: [{seq, type, category, text, location, ts}]
page_errors: [{seq, message, stack, ts}]
counts: {fatal, error, warning, info, debug, total}
collected_at
```

## Classification

- console `error` → **error**; `warning`/`warn` → **warning**; `info` → **info**;
  `log`/`debug`/… → **debug**.
- uncaught page errors (`pageerror`) → **fatal** (counted in `console_counts.fatal`
  and `page_errors`).

## Failure modes (all set `failure_reason`)

`http_fallback_not_allowed`, `browser_runtime_missing`, `missing_server_url`,
`url_not_allowed`, `console_error_present` (only when `fail_on_console_error`).

## Safety / lifecycle

- Never starts or kills the server; never touches the server session.
- Uses context managers / explicit close for the browser; `browser_closed=true`.
- Localhost-only.

## Out of scope (this round)

`full_browser_vite_login_bug_e2e` (still blocked); promotion to staging.
