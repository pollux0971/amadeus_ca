# Candidate Summary — start_local_server (v1 → v1.1)

> **v1.1 update.** Adds an optional keep-alive + teardown handoff on top of v1.
> `keep_alive=false` is unchanged. See "v1.1 keep-alive" below.

## What failed before

- v1 (vs stable): the stable `start_local_server` is a placeholder returning a
  fabricated `http://localhost:5173/`; it never launches a process.
- v1's gap (this update): v1 always terminates the server in `finally`. That is
  safe for single-skill tests but leaves no way to hand a live server to a later
  step (e.g. a future browser skill).

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

### v1.1 keep-alive

- Skill: new `keep_alive` (+ `lease_ttl_sec`, `teardown_policy`) inputs. When
  `keep_alive=true` and the server starts, it leaves the process + sandbox alive,
  emits `server_session.json`, and returns `server_session`. A new idempotent
  `teardown(session)` helper kills the process group and removes the sandbox.
- Orchestrator: threads `keep_alive` from the eval task, collects every
  `server_session` produced during a run, and tears them all down in a `finally`
  (mirror of `teardown`) so no server outlives the eval. The skill-execution
  body was extracted into `_run_skills_and_score` so the teardown `finally`
  wraps the whole run.
- `evals/server/keep_alive_smoke.yaml`: end-to-end keep-alive run (`keep_alive:
  true`) → score 1.0, then orchestrator teardown leaves nothing lingering.

## Tests added

`harnesses/candidates/start_local_server_v1/tests/test_start_local_server_v1.py`:
- `test_detect_vite_dev_command` — package.json `dev` → `npm run dev`
- `test_detect_start_command_fallback_and_explicit_override` — `start`→`npm start`; explicit wins
- `test_unsafe_command_blocked` — `sudo ...` blocked by the Safety Gate, never launched
- `test_localhost_url_detected_and_artifacts` — real launch detects URL; 3 artifacts written
- `test_process_cleanup_no_lingering` — keep_alive=false: process gone after return
- `test_timeout_failure_reason_and_cleanup` — no-URL command times out and is killed
- `test_fixture_not_mutated` — source fixture unchanged after a run
- `test_keep_alive_true_does_not_cleanup_immediately` — keep_alive=true leaves the
  process alive and writes `server_session.json` with all 8 required fields
- `test_teardown_kills_and_is_idempotent` — teardown kills the group; second call
  (and a call by session-file path) does not raise

`tests/unit/test_server_keep_alive_e2e.py`:
- `test_keep_alive_session_is_torn_down_after_eval` — keep_alive eval scores 1.0,
  a session is created, and the orchestrator's finally cleanup leaves no lingering
  process and removes the sandbox.

## Tests run

- `python scripts/validate_structure.py` — PASS
- `python scripts/validate_workflows.py` — PASS
- `python scripts/run_skill_tests.py` — 5/5 PASS
- `python scripts/run_unit_tests.py` — **62/62 PASS** (59 prior + 3 keep-alive)
- No lingering `node`/`http.server`/`sleep` processes or `server_ws_` temp dirs
  after the full run.
- (Cross-check) `vite_login_bug` still 1.0 (keep_alive defaults false);
  `keep_alive_smoke` 1.0 with end-of-run teardown.

## Remaining risks

- **Handoff consumer is out of scope.** keep_alive keeps the server up and exposes
  `server_url`, but the real consumer (a browser skill) does not exist yet; the
  placeholder browser steps do not actually connect.
- **Reader thread + memory during keep_alive.** While a server is kept alive the
  stdout reader thread stays open and accumulates the log in memory until
  teardown. Fine for short-lived demo servers; a long-lived server would need log
  rotation / a bounded buffer.
- **Lease is advisory.** `lease_ttl_sec` is recorded in the session but not yet
  enforced by a reaper; cleanup relies on the orchestrator's end-of-run teardown
  (or an explicit `teardown` call). A crash between start and teardown could leave
  one server until the OS/session ends.
- **`shell=True`** (matches the stable CLI agent style) — mitigated by the Safety
  Gate, sandbox cwd, process-group kill, and timeout, but it is a real surface.
- **Denylist gate**: a novel-but-harmful operator-authored `start_command` would
  pass. `start_command` is trusted operator input (eval/inspect), not untrusted
  content.
- **npm-dependent auto-detection**: `npm run dev`/`npm start` need `npm` on PATH.

## Promotion recommendation

Keep at `dev`. Like the patch runner, it executes shell commands, so promotion
needs human review (`promotion_policy.md`). Before a staging review: add a real
keep-alive consumer (browser skill) end-to-end, and a lease reaper so a kept-alive
server cannot survive an orchestrator crash.

## Files

New (candidate): `candidate.yaml`, `SKILL.md`, `scripts/start_local_server.py`,
`fixtures/tiny_node_server/{package.json,server.js}`,
`tests/test_start_local_server_v1.py`, `candidate_summary.md`.

New (v1.1): `evals/server/keep_alive_smoke.yaml`,
`tests/unit/test_server_keep_alive_e2e.py`.

Changed (harness infrastructure only): `src/orchestrator/orchestrator.py`
(eval start_command/keep_alive threading; session teardown in a run-end finally),
`evals/cli_browser_integration/vite_login_bug.yaml` (dep-free start_command).

Untouched (per constraints): stable `skills/` manifests, `safety_gate`,
`promotion_policy`, and the `open_localhost_browser` / `read_browser_console`
skills.
