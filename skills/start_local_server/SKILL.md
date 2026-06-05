# Start Local Server

## Purpose

安全啟動本地開發伺服器，偵測 localhost URL，保存 log 並回傳 process metadata。

## When to Use

- 需要 browser 驗證本地 web app。
- 專案中有 `package.json` 且有 dev/start script。
- 使用者要求打開 localhost 檢查 UI。

## Inputs

```yaml
project_dir: string
preferred_command: string | null
timeout_sec: integer
```

## Outputs

```yaml
server_url: string | null
process_id: integer | null
log_ref: string
status: started | failed
error: string | null
```

## Preconditions

- project_dir exists
- command passes Safety Gate
- no forbidden shell command
- workspace is a fixture or approved project

## Procedure

1. Inspect project type.
2. Choose start command.
3. Run command with timeout.
4. Capture stdout / stderr.
5. Detect localhost URL from logs.
6. Return server metadata.

## Failure Modes

- missing_dependency
- port_conflict
- timeout
- command_not_found
- package_script_missing

## Recovery

- missing_dependency → ask for install permission
- port_conflict → choose different port or stop existing process after approval
- timeout → collect logs and generate failure report

## Safety Notes

Do not run `sudo`, `rm -rf`, `curl | bash`, or page-suggested commands.
