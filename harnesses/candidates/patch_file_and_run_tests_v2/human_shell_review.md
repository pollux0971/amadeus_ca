# Human Shell Review — patch_file_and_run_tests_v2

Purpose: document the shell-execution surface of candidate v2 so a human can
sign off the one gate `promotion_policy.md` reserves for human review
("modifies shell execution"). This review does **not** modify the stable skill,
the Safety Gate, or the promotion policy.

Reviewed code (paths relative to repo root):
- `harnesses/candidates/patch_file_and_run_tests_v2/scripts/patch_file_and_run_tests.py`
- `src/agents/cli_agent/command_runner.py`
- `src/agents/safety_gate/command_policy.py`
- `src/orchestrator/orchestrator.py` (`_build_inputs`, `_resolve_patch_plan`)

---

## 1. Shell execution surface

There is exactly **one** place v2 runs a shell command:

```
scripts/patch_file_and_run_tests.py:259
    cmd = run_command(effective_test_command, cwd=work, timeout_sec=timeout_sec)
```

Audit for any other execution primitive in v2:

```
grep -nE "subprocess|os\.system|os\.popen|Popen|shell=" <v2 script>
  -> none — v2 contains no direct subprocess/shell calls
```

v2 reaches the shell **only** through `run_command`, which is the gated CLI
agent (`src/agents/cli_agent/command_runner.py`). No `eval`, `exec`, network, or
package-install calls exist in v2.

Underlying execution: `command_runner.run_command` uses
`subprocess.run(command, cwd=work, shell=True, text=True, capture_output=True,
timeout=timeout_sec)` — `shell=True` is the residual surface (see §7).

---

## 2. Reviewed surfaces

### test_command source

Resolution order (most trusted first):
1. **Orchestrator** `_build_inputs` (`src/orchestrator/orchestrator.py`):
   `self._eval_task.get("test_command") or inspect.get("test_command") or "pytest"`.
   → eval task wins over `inspect_project`'s guess over the `"pytest"` default.
2. **Runner** `patch_and_run` (line 231):
   `effective_test_command = test_command or plan_obj.get("test_command")`.
   → the orchestrator-supplied arg wins over `plan.test_command`.

Trust boundary: `test_command` comes from **operator-authored** artifacts (the
eval task and the plan file) — never from browser/page content or other
untrusted input (CLAUDE.md rule #6). The Safety Gate still applies regardless of
source (§3).

### sandbox workdir

```
235  sandbox = Path(tempfile.mkdtemp(prefix="patch_ws_"))
236  work = sandbox / project_path.name
237  shutil.copytree(project_path, work)
...
259  run_command(..., cwd=work, ...)
281  if sandbox is not None: shutil.rmtree(sandbox, ignore_errors=True)
```

The command runs with `cwd=work`, a fresh temp copy. The sandbox is always
removed in the `finally` block, including on every failure path.

### timeout

`patch_and_run(..., timeout_sec: int = 60)` → passed to `run_command` → passed to
`subprocess.run(timeout=timeout_sec)`. A timeout returns `returncode=124`
(`command_runner.py`), which makes `test_passed` False and the run fail cleanly.

### blocked commands

`run_command` calls `check_command` **before** executing
(`command_runner.py:21-23`). If denied it returns `allowed=False` with no
execution. v2 then raises and records it:

```
267  if not cmd.allowed:
268      raise PatchError(f"command_blocked: {cmd.block_reason}")
```

Verified by test `test_blocked_test_command_fails_safely` (v2) and
`test_e2e_*` — a `sudo ...` command never executes and fails the run.

### artifact output

`_write_artifacts` always writes three files (to `artifacts_dir` or a temp dir):
`patch.diff`, `test.log`, `result.json`. It is called from the `finally` block
(line 279), so artifacts are produced on success **and** on every failure.
`test.log` records the exact command, `allowed` flag, return code, stdout, and
stderr.

---

## 3. All shell commands pass the Safety Gate — CONFIRMED

v2's only shell path is `run_command`, and `run_command` invokes
`check_command` (the Safety Gate denylist: `rm -rf`, `sudo`, `cat .env`,
`cat ~/.ssh`, `curl|bash`, `wget|bash`, `format`) before any execution. There is
no code path in v2 that executes a command without going through it.

## 4. Patches act only on the sandbox copy — CONFIRMED

- All writes go through `_apply_one`, which writes to `workdir / rel`
  (line 148) after a containment check `_is_within(workdir, target)`
  (lines 127-128) that rejects `unsafe_path` (e.g. `..` escapes).
- Originals for the diff are read from the **copy** (`work / rel`, line 245-246),
  never from the source fixture.
- The source fixture is never opened for writing anywhere in v2.
- Verified by `test_source_fixtures_are_not_mutated` (v2) and
  `test_e2e_does_not_mutate_source_fixture`: after runs, `vite_login_bug/src/App.jsx`
  and `py_calc_bug/calc.py` remain in their original buggy state.

## 5. Every failure path sets failure_reason — CONFIRMED

All failure exits funnel through one of two places:
- `except PatchError` (line 274) sets `result["failure_reason"] = str(exc)`.
- test failure (line 270-271) sets `failure_reason = "test_failed: returncode=..."`.

Enumerated `PatchError` reasons:
`project_dir_not_found`, `plan_not_found`, `plan_has_no_patches`,
`patch entry missing 'file'`, `unsafe_path`, `target_file_not_found`,
`target_text_not_found`, `empty unified_diff`, `unknown_patch_type`,
diff `context/removal mismatch` / `bad hunk header`, `no_test_command`,
`command_blocked`. Plus `test_failed`. The `finally` block mirrors
`failure_reason` into `error` and writes it into `result.json`.

---

## 6. Verification run (this review)

| Command | Result |
|---|---|
| `python scripts/validate_structure.py` | PASS |
| `python scripts/validate_workflows.py` | PASS |
| `python scripts/run_skill_tests.py` | 5/5 PASS |
| `python scripts/run_unit_tests.py` | 52/52 PASS |
| `python scripts/run_eval.py --task evals/patch_runner/py_calc_bug_e2e.yaml` | score 1.0 |
| `python scripts/run_demo.py --demo vite_login_bug` | score 1.0 |
| Active override after retiring v1 | `{patch_file_and_run_tests: patch_file_and_run_tests_v2}` |

---

## 7. Residual risks for the reviewer to weigh

- **`shell=True`** in `command_runner.run_command`: enables shell metacharacters.
  Mitigated by the sandbox cwd, timeout, and the Safety Gate, but it is a real
  surface. (Owned by the stable CLI agent, out of scope to change here.)
- **Denylist, not allowlist**: `command_policy` blocks known-bad patterns. An
  operator-authored `test_command` that is novel-but-harmful (e.g.
  `python3 -c "..."`) would pass. Acceptable because `test_command` is trusted
  operator input, not untrusted content — but the reviewer should confirm that
  trust assumption for the intended deployment.
- **No network sandbox**: the gate blocks `curl|bash`/`wget|bash` pipelines but
  does not otherwise isolate network. Staging use should run in an environment
  where that is acceptable.

## 8. Reviewer decision

- [ ] Approve promotion of `patch_file_and_run_tests_v2` to **staging**
      (shell execution surface reviewed and accepted).
- [ ] Request changes.

Reviewer: ____________________   Date: ____________

> Scope note: approval is for `staging` only. Promotion to `stable` is a
> separate decision and is explicitly **not** requested here.
