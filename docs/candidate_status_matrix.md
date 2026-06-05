# Candidate Status Matrix

Snapshot of every harness candidate under `harnesses/candidates/`. The harness
overlay resolver activates, per overridden skill, the highest-`version`
candidate whose `candidate.yaml` has `active: true`.

> Key facts encoded below and enforced by `scripts/validate_candidate_docs.py`:
> **read_browser_console is blocked**, **open_localhost_browser requires a
> Playwright gate**, and **http_fallback is not a real browser**.

| Candidate | Overrides | Active | Version | Stage | Tests passed | E2E status | Remaining blockers | Promotion recommendation |
|---|---|---|---|---|---|---|---|---|
| `patch_file_and_run_tests_v1` | patch_file_and_run_tests | `false` | 1 | **superseded** | own unit tests pass | n/a (replaced) | superseded by v2 | Keep retired (`active:false`); do **not** delete. |
| `patch_file_and_run_tests_v2` | patch_file_and_run_tests | `true` | 2 | **staging-ready** | candidate + harness unit tests pass | `vite_login_bug` 1.0; `py_calc_bug_e2e` 1.0 | human shell-execution review sign-off before **stable** | **Staging-ready after human shell review** (then `staging`; `stable` is a separate, later decision). |
| `start_local_server_v1` (release 1.2) | start_local_server | `true` | 1.2 | **dev** (staging-candidate) | candidate + reaper + e2e unit tests pass | `keep_alive_smoke` 1.0; `vite_login_bug` 1.0 | lease is advisory (not an OS-level watchdog); real keep-alive consumer pending | Hold at `dev`/staging-candidate; needs human shell review + an OS-level guard discussion before staging. |
| `open_localhost_browser_v1` | open_localhost_browser | `true` | 1 | **dev** (blocked from staging) | candidate + e2e unit tests pass | `open_localhost_keep_alive_smoke` 1.0 **via http_fallback** (`is_real_browser=false`) | no Playwright/Chromium here → not a real browser; **real-browser gate eval + runner exist but not yet executed in a Playwright environment** (`scripts/run_playwright_gate.py`) | Keep `dev`. **Not staging** until the real-browser (Playwright) e2e in `playwright_verification_plan.md` passes. |
| `read_browser_console_not_started` | read_browser_console | n/a (no candidate yet) | — | **blocked** | n/a | n/a | requires `browser_mode=playwright` (real browser); blocked until `open_localhost_browser_v1` passes the Playwright gate | **Do not start.** A console built on `http_fallback` would be fake/empty (ADR-013). |

## Notes

- **patch_file_and_run_tests_v2** — the active patch runner. Data-driven
  (`replace_text` / `unified_diff`) with a sandbox copy; the shell-execution
  surface is reviewed in its `human_shell_review.md`.
- **start_local_server_v1.2** — real subprocess lifecycle, keep-alive + idempotent
  teardown, and a lease reaper (`reap_sessions` / `scripts/reap_server_sessions.py`).
  The lease is advisory; see its `candidate_summary.md` remaining risks.
- **open_localhost_browser_v1** — consumes the kept-alive `server_url`. In this
  environment it runs the **HTTP fallback** engine. **http_fallback is not a real
  browser**: no JS execution, no rendered DOM, no console, no screenshot. Every
  result and the run's score metrics are marked `engine=http_fallback`,
  `is_real_browser=false` (ADR-013).
- **read_browser_console** — intentionally not started; **blocked** behind the
  Playwright gate so it is never built on a fake console.

## Stage legend

- **dev** — experimental; may change.
- **staging-ready** — passed required checks; awaiting the human review the
  promotion policy reserves for shell execution.
- **blocked** — must not proceed until a named prerequisite is met.
- **superseded** — retired in favour of a newer version; kept for history.
