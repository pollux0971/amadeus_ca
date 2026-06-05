# 04 · Candidate Evolution Summary

Per-candidate stage, result, and remaining risk. Full detail lives in each
candidate's `harnesses/candidates/<id>/candidate_summary.md`.

## patch_file_and_run_tests_v1 — demo-specific

- **Stage:** superseded (`active:false`, kept for history).
- **Result:** took `vite_login_bug` from 0.667 → 1.0 by applying the known
  `App.jsx` fix on a sandbox copy and running the test command through the Safety
  Gate.
- **Remaining risk:** hard-coded fix; not a general patch tool → not promotable.

## patch_file_and_run_tests_v2 — plan-driven reusable patch runner

- **Stage:** **staging-ready after human shell review.**
- **Result:** declarative `patch_plan` (`replace_text` + `unified_diff`) applied
  to a sandbox copy, emitting a real `patch.diff`; runs the eval's `test_command`
  through the Safety Gate. Proven on `vite_login_bug` (1.0) and a non-vite
  `py_calc_bug` end-to-end (1.0). No fixture-specific code.
- **Remaining risk:** executes a shell command → needs a human shell-execution
  review before `stable`; the diff applier handles clean diffs only.

## start_local_server_v1 — subprocess server lifecycle

- **Stage:** folded into v1.2.
- **Result:** real `Popen` server launch in its own process group, localhost-URL
  detection within a timeout, artifacts, and guaranteed cleanup.
- **Remaining risk:** v1 always killed the server (no handoff).

## start_local_server_v1.1 — keep_alive + teardown handoff

- **Stage:** folded into v1.2.
- **Result:** `keep_alive=true` leaves the server + sandbox alive and emits
  `server_session.json`; idempotent `teardown(session)`; the orchestrator tears
  down kept-alive sessions in a `finally`. `keep_alive=false` unchanged.
- **Remaining risk:** the live-server consumer (a real browser) did not exist yet.

## start_local_server_v1.2 — lease reaper

- **Stage:** **dev / staging-candidate.**
- **Result:** sessions record `started_at` + `lease_ttl_sec` and register to a
  `_sessions` dir; `reap_sessions` / `scripts/reap_server_sessions.py` reap stale
  servers (idempotent; dry-run; corrupt JSON reported, not crashing).
- **Remaining risk:** the lease is **advisory — not an OS-level watchdog**;
  executes shell commands (needs human review before staging).

## open_localhost_browser_v1 — HTTP fallback smoke + real-browser gate pending

- **Stage:** **dev** (blocked from staging).
- **Result:** consumes the kept-alive `server_url`; localhost-only; layered engine
  (Playwright → HTTP fallback). Smoke e2e 1.0 via the fallback; every result is
  marked `engine`, `is_real_browser`, `screenshot/js/console_supported`.
- **Remaining risk:** **http_fallback is not a real browser** (no JS/DOM/console/
  screenshot). Must pass the Playwright gate before staging. **read_browser_console
  is blocked** on this.

## read_browser_console — not started (blocked)

- **Stage:** **blocked.** No candidate.
- **Reason:** must depend on `browser_mode=playwright`; a console on the HTTP
  fallback would be fake. Do not start until the Playwright gate passes.
