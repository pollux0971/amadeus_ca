# Candidate Summary — start_local_server_v1

## What failed before

The stable `start_local_server` skill is a placeholder: it returns a fabricated
`http://localhost:5173/` from a hard-coded fake log and never launches a process.
Nothing is actually started, nothing is cleaned up, and no real artifacts exist.

## What changed

A real subprocess server-lifecycle runner (no stable skill / safety gate /
promotion policy changed):

- Copies the fixture to a sandbox; the source fixture is never mutated.
- Resolves the start command: explicit `start_command` > `package.json` scripts
  (`dev` → `npm run dev`, else `start` → `npm start`) > `preferred_command`.
- Checks the command against the **Safety Gate** before launching.
- `subprocess.Popen(..., shell=True, start_new_session=True)` so the server has
  its own process group.
- Reads merged stdout/stderr in a thread, matching
  `https?://(localhost|127.0.0.1):\d+` within `timeout_sec`.
- Writes `server.log`, `result.json`, `process.json`.
- **Always** terminates the process group (SIGTERM→SIGKILL) in `finally`, so no
  process lingers on success or failure. Every failure path sets `failure_reason`.

Harness wiring (infrastructure, not the stable skill manifest/safety/promotion):
- `src/orchestrator/orchestrator.py`: threads eval-task `start_command` /
  `server_timeout_sec` into the skill (stable placeholder ignores the extras).
- `evals/cli_browser_integration/vite_login_bug.yaml`: adds a dep-free
  `start_command` (`python3 -u -m http.server 0 --bind 127.0.0.1`) so the now-real
  server skill can serve the vite fixture without installing vite/node_modules,
  keeping the slice at 1.0.

## Tests added

`harnesses/candidates/start_local_server_v1/tests/test_start_local_server_v1.py`:
- `test_detect_vite_dev_command` — package.json `dev` → `npm run dev`
- `test_detect_start_command_fallback_and_explicit_override` — `start`→`npm start`; explicit wins
- `test_unsafe_command_blocked` — `sudo ...` blocked by the Safety Gate, never launched
- `test_localhost_url_detected_and_artifacts` — real launch detects URL; 3 artifacts written
- `test_process_cleanup_no_lingering` — launched process is gone after return
- `test_timeout_failure_reason_and_cleanup` — no-URL command times out and is killed
- `test_fixture_not_mutated` — source fixture unchanged after a run

## Tests run

- `python scripts/validate_structure.py` — PASS
- `python scripts/validate_workflows.py` — PASS
- `python scripts/run_skill_tests.py` — 5/5 PASS
- `python scripts/run_unit_tests.py` — **59/59 PASS** (52 prior + 7 v1)
- No lingering `node`/`http.server`/`sleep` processes after the full run.
- (Cross-check) `vite_login_bug` still 1.0 with a real server step;
  `active_overrides = {patch_file_and_run_tests: v2, start_local_server: v1}`.

## Remaining risks

- **Detect-and-cleanup, not handoff.** v1 kills the server right after reading
  the URL, so it does not yet provide a live server to a downstream browser
  skill. In the vite slice the browser/console steps are still placeholders, so
  this is fine today; a real browser integration will need a "keep alive + return
  a handle/teardown" mode.
- **`shell=True`** (matches the stable CLI agent style) — mitigated by the Safety
  Gate, sandbox cwd, process-group kill, and timeout, but it is a real surface.
- **Denylist gate**: a novel-but-harmful operator-authored `start_command` would
  pass. `start_command` is trusted operator input (eval/inspect), not untrusted
  content.
- **npm-dependent auto-detection**: `npm run dev`/`npm start` need `npm` on PATH;
  fixtures without it must pass an explicit `start_command`.
- **Port handling** is delegated to the command (e.g. `http.server 0` for an
  OS-assigned port); v1 does not itself allocate or guarantee a free port.

## Promotion recommendation

Keep at `dev`. Like the patch runner, it executes shell commands, so promotion
needs human review (`promotion_policy.md`). Before a staging review: add the
keep-alive/teardown handoff mode and at least one non-vite end-to-end eval that
consumes the live server.

## Files

New (candidate): `candidate.yaml`, `SKILL.md`, `scripts/start_local_server.py`,
`fixtures/tiny_node_server/{package.json,server.js}`,
`tests/test_start_local_server_v1.py`, `candidate_summary.md`.

Changed (harness infrastructure only): `src/orchestrator/orchestrator.py`
(eval start_command threading), `evals/cli_browser_integration/vite_login_bug.yaml`
(dep-free start_command).

Untouched (per constraints): stable `skills/` manifests, `safety_gate`,
`promotion_policy`, and the `open_localhost_browser` / `read_browser_console`
skills.
