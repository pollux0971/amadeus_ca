# Candidate Summary — start_local_server (v1 → v1.1 → v1.2)

> **v1.2 update.** Adds a lease reaper on top of the v1.1 keep-alive handoff.
> `keep_alive=false` is unchanged and `keep_alive=true` handoff is preserved.
> See "v1.2 lease reaper" below.

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

### v1.2 lease reaper

- Session now records `started_at` and is registered to an optional
  `sessions_dir` (`<server_id>.json`) so it is discoverable after a crash.
- New `reap_sessions(sessions_dir/runs_dir, now, dry_run, report_path)`: marks a
  session stale when `now > started_at + lease_ttl_sec`, tears down stale ones
  (kill group + remove sandbox + unlink registry) via the idempotent `teardown`,
  keeps non-stale ones, reports corrupt/incomplete JSON in `errors` without
  crashing, and supports `dry_run`. `scripts/reap_server_sessions.py` is a manual
  CLI.
- Orchestrator: passes `sessions_dir = <runs>/_sessions` and de-registers each
  session on clean teardown, so the registry is empty after a normal run and a
  leftover file only exists if the orchestrator crashed.

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

`harnesses/candidates/start_local_server_v1/tests/test_lease_reaper.py`:
- `test_expired_session_is_reaped` — stale server killed; sandbox + registry removed
- `test_non_expired_session_is_kept` — within lease: untouched, still running
- `test_missing_process_handled_idempotently` — already-dead session reaped, no error
- `test_corrupt_session_reported_not_crash` — corrupt/incomplete JSON → `errors`
- `test_dry_run_does_not_kill_or_delete` — dry_run reports only
- `test_reaper_writes_report_and_skips_its_own_report`

`tests/unit/test_server_keep_alive_e2e.py`:
- `test_keep_alive_session_is_torn_down_after_eval` — keep_alive eval scores 1.0,
  a session is created, and the orchestrator's finally cleanup leaves no lingering
  process, removes the sandbox, and de-registers the session.

## Tests run

- `python scripts/validate_structure.py` — PASS
- `python scripts/validate_workflows.py` — PASS
- `python scripts/run_skill_tests.py` — 5/5 PASS
- `python scripts/run_unit_tests.py` — **68/68 PASS** (62 prior + 6 reaper)
- `python scripts/run_eval.py --task evals/patch_runner/py_calc_bug_e2e.yaml` — 1.0
- `python scripts/run_demo.py --demo vite_login_bug` — 1.0
- No lingering `node`/`http.server`/`sleep` processes, `server_ws_` temp dirs,
  or leftover `_sessions` registry entries after the full run.
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
- **Crash residual — mitigated, not eliminated.** A crash between start and the
  orchestrator's finally teardown leaves the kept-alive server running. v1.2's
  lease reaper mitigates this: the session is registered under `<runs>/_sessions`
  and `reap_sessions` / `scripts/reap_server_sessions.py` tears it down once the
  lease expires. But the lease is **advisory** — it is only enforced when the
  reaper actually runs (end-of-run teardown, an explicit call, or a scheduled
  job). It is **not an OS-level watchdog**, so between a crash and the next reaper
  run a stale server can still exist for up to `lease_ttl_sec` (plus the reaper
  interval). A future version could register an OS-level cgroup/systemd-scope or
  a supervised reaper for hard guarantees.
- **`shell=True`** (matches the stable CLI agent style) — mitigated by the Safety
  Gate, sandbox cwd, process-group kill, and timeout, but it is a real surface.
- **Denylist gate**: a novel-but-harmful operator-authored `start_command` would
  pass. `start_command` is trusted operator input (eval/inspect), not untrusted
  content.
- **npm-dependent auto-detection**: `npm run dev`/`npm start` need `npm` on PATH.

## Promotion recommendation

Keep at `dev`. Like the patch runner, it executes shell commands, so promotion
needs human review (`promotion_policy.md`). The lease-reaper item is now done
(v1.2). Before a staging review: add a real keep-alive consumer (browser skill)
end-to-end, and consider an OS-level guard (cgroup/systemd-scope or a supervised
reaper) if hard crash-residual guarantees are required.

## Files

New (candidate): `candidate.yaml`, `SKILL.md`, `scripts/start_local_server.py`,
`fixtures/tiny_node_server/{package.json,server.js}`,
`tests/test_start_local_server_v1.py`, `candidate_summary.md`.

New (v1.1): `evals/server/keep_alive_smoke.yaml`,
`tests/unit/test_server_keep_alive_e2e.py`.

New (v1.2): `scripts/reap_server_sessions.py`, `tests/test_lease_reaper.py`
(reap_sessions lives in `scripts/start_local_server.py`).

Changed (harness infrastructure only): `src/orchestrator/orchestrator.py`
(eval start_command/keep_alive threading; sessions_dir registry; session
teardown + de-register in a run-end finally),
`evals/cli_browser_integration/vite_login_bug.yaml` (dep-free start_command).

Untouched (per constraints): stable `skills/` manifests, `safety_gate`,
`promotion_policy`, and the `open_localhost_browser` / `read_browser_console`
skills.
