# Patch File And Run Tests

## Purpose

套用最小程式碼修改，然後執行測試，回傳 test result 與 git diff。

## When to Use

- 已經定位到 source file。
- 有明確 bug cause。
- 修復後需要驗證。
- Candidate patch loop 需要測試。

## Inputs

```yaml
project_dir: string
patch: string
test_command: string
```

## Outputs

```yaml
patch_applied: boolean
test_passed: boolean
test_output_ref: string
diff_ref: string
status: passed | failed
```

## Preconditions

- project_dir exists
- patch is limited to workspace
- command passes Safety Gate

## Procedure

1. Validate patch path.
2. Apply patch.
3. Run tests with timeout.
4. Capture stdout / stderr.
5. Save diff.
6. Return result.

## Failure Modes

- patch_conflict
- test_failed
- command_blocked
- timeout
- unsafe_path

## Safety

Never patch outside workspace. Never remove safety tests to make tests pass.
