# Start Local Server — Candidate v1.2

## Status

`dev` candidate, `version: 1.2`, overrides the stable `start_local_server`
placeholder when candidate overlays are enabled (the orchestrator enables them;
a bare `SkillExecutor("skills")` runs the stable skill).

## What it does

Launches a real local dev server as a subprocess, detects its localhost URL, and
writes artifacts. First version targets local Node/Vite-style fixtures.

v1.1 adds an optional **keep-alive + teardown handoff**:
- `keep_alive=false` (default): start, detect, write artifacts, then always
  terminate the process group in `finally` (unchanged v1 behavior).
- `keep_alive=true`: leave the process + sandbox alive and emit
  `server_session.json` so a later step can use `server_url`. Tear it down with
  `teardown(session)` (idempotent). The orchestrator tears down any kept-alive
  sessions at the end of an eval run.

## Inputs

```yaml
project_dir: string            # fixture path
preferred_command: string|null # inspect_project's guess (fallback)
start_command: string|null     # explicit override (highest priority)
timeout_sec: integer           # default 30
artifacts_dir: string|null     # where to write artifacts
keep_alive: boolean            # default false; true -> handoff a live server
lease_ttl_sec: integer         # default 300; advisory lease recorded in session
teardown_policy: string        # default "process_group"
sessions_dir: string|null      # registry dir for the reaper (<id>.json)
```

## Outputs

```yaml
status: started | failed
server_url: string | null
process_id: integer | null
command: string | null
keep_alive: boolean
server_session: object | null  # present when keep_alive succeeded
log_ref / result_ref / process_ref: string
server_session_ref: string | null
failure_reason: string | null
```

## server_session.json (keep_alive=true)

```yaml
server_id: string        # uuid
server_url: string
pid: integer
pgid: integer
workdir: string          # sandbox copy the server runs in
log_ref: string
started_at: float        # epoch seconds at launch (lease basis)
lease_ttl_sec: integer
teardown_policy: string
session_file: string|null  # registry path, when sessions_dir is given
```

## teardown(session)

`teardown(session_dict_or_path)` kills the process group and removes the
sandbox. **Idempotent** — calling it again after the server is gone returns
`{torn_down: true, killed: false}` and never raises.

## Lease + reaper (v1.2)

A kept-alive session records `started_at` and `lease_ttl_sec` (default 300s). It
is also written to an optional `sessions_dir` registry (`<server_id>.json`) so a
reaper can find it if the caller crashes before teardown.

`reap_sessions(sessions_dir=None, runs_dir=None, now=None, dry_run=False,
report_path=None)`:
- scans the registry dir (`*.json`) and/or a runs tree (`server_session.json`);
- a session is **stale** when `now > started_at + lease_ttl_sec`;
- stale → `teardown` (kill group + remove sandbox) and the registry file is
  removed; non-stale → kept untouched;
- already-dead pid/pgid → idempotent, no error;
- corrupt / incomplete session JSON → recorded in `errors`, never crashes;
- `dry_run=true` → reports what would be reaped, kills/deletes nothing;
- returns a report and optionally writes it to `report_path`.

Manual run: `scripts/reap_server_sessions.py --sessions-dir runs/_sessions`
(or `--runs-dir runs --dry-run`). The orchestrator registers kept-alive sessions
under `<runs>/_sessions` and de-registers them on clean teardown, so the reaper
only ever finds sessions left behind by a crash.

The lease is **advisory**: it is enforced only when the reaper runs (the
orchestrator's end-of-run teardown, an explicit `teardown`, or a scheduled
reaper). It is not an OS-level watchdog.

## Command resolution

1. explicit `start_command`
2. `package.json` scripts — `dev` (→ `npm run dev`), else `start` (→ `npm start`)
3. `preferred_command`

## Procedure

1. Copy the fixture to a sandbox (the source is never mutated).
2. Resolve the start command and check it against the **Safety Gate**.
3. `subprocess.Popen(..., shell=True, start_new_session=True)` — own process group.
4. Read merged stdout/stderr in a thread; match `https?://(localhost|127.0.0.1):\d+`.
5. On URL within `timeout_sec` → `status: started`. Else `timeout_no_url`, or
   `server_exited_early` if the process died first.
6. In `finally`, write `server.log`, `result.json`, `process.json`, then:
   - `keep_alive=false` → `killpg` the process group (SIGTERM→SIGKILL) and
     remove the sandbox (nothing lingers).
   - `keep_alive=true` (only on `started`) → write `server_session.json` and
     leave the process + sandbox alive; the caller/orchestrator calls
     `teardown(session)` later.

## Failure modes (all set `failure_reason`)

`project_dir_not_found`, `no_start_command`, `command_blocked`, `spawn_error`,
`server_exited_early`, `timeout_no_url`.

## Safety

- Start command runs only after passing the Safety Gate; a blocked command never
  launches.
- All writes happen in a temp sandbox; the source fixture is never modified.
- `keep_alive=false`: the process group is always terminated. `keep_alive=true`:
  the process is handed off and torn down via `teardown` / the orchestrator's
  end-of-run cleanup, so it never outlives the eval.

## Scope / limits

- `keep_alive=true` keeps the server up for a later step's `server_url`, but the
  consumer (a real browser skill) is out of scope here — the placeholder browser
  skills do not actually connect yet.
- `keep_alive` holds the stdout reader thread open and accumulates the log in
  memory until teardown; fine for short-lived demo servers.
- Out of scope (per task): open_localhost_browser, read_browser_console.

## Proven on

- `fixtures/tiny_node_server` (in-candidate) — `npm run dev` → node http server.
- `fixtures/vite_login_bug` via the orchestrator with an eval-provided dep-free
  `start_command` (`python3 -u -m http.server`).
