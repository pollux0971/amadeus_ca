# Start Local Server — Candidate v1

## Status

`dev` candidate, `version: 1`, overrides the stable `start_local_server`
placeholder when candidate overlays are enabled (the orchestrator enables them;
a bare `SkillExecutor("skills")` runs the stable skill).

## What it does

Launches a real local dev server as a subprocess, detects its localhost URL,
writes artifacts, and always cleans the process up. First version targets local
Node/Vite-style fixtures.

## Inputs

```yaml
project_dir: string            # fixture path
preferred_command: string|null # inspect_project's guess (fallback)
start_command: string|null     # explicit override (highest priority)
timeout_sec: integer           # default 30
artifacts_dir: string|null     # where to write server.log/result.json/process.json
```

## Outputs

```yaml
status: started | failed
server_url: string | null
process_id: integer | null
command: string | null
log_ref / result_ref / process_ref: string
failure_reason: string | null
```

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
6. **Always** `killpg` the process group (SIGTERM then SIGKILL) in `finally`,
   then write `server.log`, `result.json`, `process.json`.

## Failure modes (all set `failure_reason`)

`project_dir_not_found`, `no_start_command`, `command_blocked`, `spawn_error`,
`server_exited_early`, `timeout_no_url`.

## Safety

- Start command runs only after passing the Safety Gate; a blocked command never
  launches.
- All writes happen in a temp sandbox; the source fixture is never modified.
- The process group is always terminated — success or failure — so nothing
  lingers.

## Scope / limits

- Detects-and-cleans-up: v1 terminates the server after reading the URL; it does
  not yet keep a live server for a downstream browser skill.
- Out of scope (per task): open_localhost_browser, read_browser_console.

## Proven on

- `fixtures/tiny_node_server` (in-candidate) — `npm run dev` → node http server.
- `fixtures/vite_login_bug` via the orchestrator with an eval-provided dep-free
  `start_command` (`python3 -u -m http.server`).
