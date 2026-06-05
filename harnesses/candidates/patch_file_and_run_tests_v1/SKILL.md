# Patch File And Run Tests — Candidate v1

## Status

`dev` candidate. Overrides the stable `patch_file_and_run_tests` skill **only
when the harness runs with candidate overlays enabled** (the orchestrator does;
a bare `SkillExecutor("skills")` does not).

## Scope

vite_login_bug demo only. It knows one fix: the `src/App.jsx` null-deref bug.
Do not treat this as a general patch tool.

## Inputs

```yaml
project_dir: string        # fixture path from the eval task
test_command: string       # e.g. "npm test"
patch: string              # accepted for signature compatibility; unused in v1
artifacts_dir: string      # optional; where to write patch.diff/test.log/result.json
timeout_sec: integer       # default 60
```

## Outputs

```yaml
patch_applied: boolean
test_passed: boolean
status: passed | failed
returncode: integer
diff_ref: string
test_output_ref: string
result_ref: string
error: string | null
```

## Procedure

1. Verify `project_dir` and `src/App.jsx` exist.
2. Build the fixed content (prefer the worked example `src/App.fixed.example.jsx`).
3. Compute a unified diff (`patch.diff`).
4. Copy the project to an isolated sandbox; apply the fix **there only**.
5. Run `test_command` through the Safety Gate (`run_command`), capture output.
6. Write `patch.diff`, `test.log`, `result.json`; return the result.

## Safety

- Never mutates the committed fixture — all writes happen in a temp sandbox.
- Path containment check before writing.
- Test command runs through the Safety Gate; a blocked command fails the run.
- Sandbox is removed after the run.

## Promotion notes

Executes shell commands → human review required before promotion
(see `specs/harness/promotion_policy.md`). A general version would need a real
patch format, multi-file support, and a broader eval set.
