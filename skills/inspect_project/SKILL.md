# Inspect Project

## Purpose

檢查專案目錄，判斷專案類型與可用的啟動 / 測試方式。

## When to Use

- 任務開始時。
- 需要知道專案是 Python、Node、Vite、React 或 unknown。
- 需要找出 package manager、test command、start command。

## Inputs

```yaml
project_dir: string
```

## Outputs

```yaml
project_type: string
detected_files: list[string]
start_command: string | null
test_command: string | null
notes: list[string]
```

## Preconditions

- `project_dir` exists.
- Agent has read permission.

## Procedure

1. List top-level files.
2. Check for `package.json`.
3. Check for `pyproject.toml`, `requirements.txt`, `pytest.ini`.
4. Infer start command.
5. Infer test command.
6. Return structured summary.

## Failure Modes

- directory_not_found
- permission_denied
- unknown_project_type

## Recovery

- Ask user to provide correct path.
- Fall back to generic file listing.
