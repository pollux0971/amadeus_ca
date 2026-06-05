# Patch File And Run Tests — Candidate v2

## Status

`dev` candidate, `version: 2`. Supersedes v1 via the version-aware overlay
resolver (highest active version wins). Active only when the harness runs with
candidate overlays enabled (the orchestrator does); a bare
`SkillExecutor("skills")` still runs the stable skill.

## What changed from v1

v1 hard-coded the vite `App.jsx` fix. v2 has **no fixture-specific code** — it
executes a declarative `patch_plan`. Adding support for a new bug means adding a
plan file, not changing the runner.

## patch_plan schema

```yaml
description: string            # optional
test_command: string          # optional; the runner arg overrides it
patches:
  - type: replace_text
    file: <path relative to fixture root>
    find: <exact substring, must be present>
    replace: <replacement>
    count: <int>              # optional; default replace all occurrences
  - type: unified_diff
    file: <path relative to fixture root>
    diff: |
      --- a/<path>
      +++ b/<path>
      @@ -l,s +l,s @@
       context
      -removed
      +added
```

Plans live in `plans/<fixture-basename>.yaml` and are auto-resolved from
`project_dir`'s basename when no explicit `plan` is passed.

## Inputs

```yaml
project_dir: string        # fixture path (its basename selects the plan)
test_command: string|null  # overrides plan.test_command
plan: object|null          # explicit patch_plan (skips plan-file lookup)
plans_dir: string|null     # override plans directory (defaults to ./plans)
artifacts_dir: string|null # where to write patch.diff/test.log/result.json
timeout_sec: integer       # default 60
```

## Outputs

```yaml
patch_applied: boolean
test_passed: boolean
status: passed | failed
failure_reason: string | null
target_files: [string]
returncode: integer | null
diff_ref / test_output_ref / result_ref: string
```

## Procedure

1. Resolve the plan (explicit arg or `plans/<fixture>.yaml`).
2. Copy the fixture to an isolated sandbox (the source is never mutated).
3. Apply each patch (`replace_text` / `unified_diff`) in the sandbox.
4. Emit `patch.diff` from a real before/after unified diff of every touched file.
5. Run `test_command` through the Safety Gate; capture `test.log`.
6. Write `result.json` (with `failure_reason` on failure); return the result.

## Failure modes

`plan_not_found`, `target_file_not_found`, `target_text_not_found`,
`diff_apply_failed` (context/removal mismatch), `command_blocked`,
`no_test_command`, `test_failed`, `unsafe_path`.

## Safety

- All writes happen in a temp sandbox; path containment is checked per file.
- The test command runs through the Safety Gate; a blocked command fails the run.
- Idempotent and sandboxed; the sandbox is removed after the run.

## Proven on

- `fixtures/vite_login_bug` — `replace_text` (plans/vite_login_bug.yaml)
- `fixtures/py_calc_bug` (in-candidate) — `unified_diff` (plans/py_calc_bug.yaml)
