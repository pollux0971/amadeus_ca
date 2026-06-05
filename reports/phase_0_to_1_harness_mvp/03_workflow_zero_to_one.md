# 03 · Workflow: 0→1

## The 0→1 workflow

The first goal is not a big agent but a **walking skeleton** — a thin path that
touches every core module:

```text
eval task (yaml)
  → load skill registry
  → candidate overlay resolves the implementation
  → execute skill
  → write trace.jsonl
  → evaluator → score.json (+ summary.md, failure_report.md on failure)
```

This is exercised by `scripts/run_eval.py` and `scripts/run_demo.py`. The minimal
green example is `evals/walking_skeleton/inspect_only.yaml` (runs `inspect_project`
only). The thin vertical slice is `vite_login_bug` (inspect → start server → open
browser → read console → patch + tests), now backed by real candidates.

## Skill execution flow

For each required skill the orchestrator: builds inputs (threading prior outputs
via the blackboard), runs the skill through the overlay-resolved executor, logs a
trace event, collects evidence, and (for kept-alive servers) registers a session
for end-of-run teardown. The evaluator then maps evidence → criteria → score.

## Candidate evolution in this phase

### patch_file_and_run_tests: v1 → v2

- **v1** — made `vite_login_bug` reach 1.0 by applying the *known* `App.jsx` fix
  on a sandbox copy and running the test command through the Safety Gate. Honest,
  but **demo-specific** (hard-coded fix) → not promotable.
- **v2** — a **plan-driven, reusable** patch runner: a declarative `patch_plan`
  with `replace_text` and `unified_diff`, applied to a sandbox copy, emitting a
  real `patch.diff`. Proven on two unrelated fixtures (vite + an in-candidate
  `py_calc_bug`) and exercised end-to-end via the orchestrator. v1 retired
  (`active:false`, superseded — not deleted).

### start_local_server: v1 → v1.2

- **v1** — real `subprocess` server lifecycle: sandbox copy, command resolution
  (explicit > package.json dev/start > preferred), Safety Gate check, launch in
  its own process group, detect the localhost URL within a timeout, always clean
  up.
- **v1.1** — **keep_alive + teardown handoff**: with `keep_alive=true` the server
  stays alive (emitting `server_session.json`) so a later step can use its
  `server_url`; the orchestrator tears every kept-alive session down in a
  `finally`. `keep_alive=false` keeps the original cleanup behavior.
- **v1.2** — **lease reaper**: sessions record `started_at` + `lease_ttl_sec` and
  register to a `_sessions` dir; `reap_sessions` / `scripts/reap_server_sessions.py`
  cleans up stale servers left by a crash. The lease is advisory (not an OS-level
  watchdog).

### open_localhost_browser: v1 (current)

- Consumes the kept-alive `server_url`, loads the page, builds a snapshot, and
  writes artifacts. It uses a **layered engine**: Playwright when available, else
  an **HTTP fallback**. In this environment there is no Playwright, so it runs the
  fallback — `engine=http_fallback`, `is_real_browser=false`. The smoke e2e is
  1.0, but **this is not a real browser**.

## Why read_browser_console is blocked

A console skill needs a real browser: JavaScript execution and an actual browser
console. The HTTP fallback has neither — a console built on it would report a
**fake/empty console** and silently corrupt every downstream evaluation. So
`read_browser_console` is **blocked by policy** (ADR-013) until the Playwright
real-browser gate passes. This is a deliberate correctness decision, not an
unfinished task.
