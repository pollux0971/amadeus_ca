# Open Localhost Browser

## Purpose

打開本地 server URL，擷取頁面摘要、標題、可互動元素與初始 console 狀態。

## When to Use

- server_url 已由 `start_local_server` 取得。
- 需要驗證本地 web app。
- 需要 browser evidence。

## Inputs

```yaml
server_url: string
wait_until: load | networkidle | domcontentloaded
```

## Outputs

```yaml
url: string
title: string
dom_summary: string
screenshot_ref: string | null
console_errors: list[string]
status: opened | failed
```

## Preconditions

- server_url starts with localhost or 127.0.0.1
- Browser automation is available

## Procedure

1. Validate URL is local.
2. Open browser page.
3. Wait for load.
4. Collect title.
5. Extract DOM summary.
6. Collect console errors.
7. Save screenshot.

## Failure Modes

- browser_not_available
- page_load_timeout
- invalid_url
- server_not_running
