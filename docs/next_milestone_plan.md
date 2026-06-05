# Next Milestone Plan

Ordered plan after the candidate-status review. Each step has an explicit gate;
do not skip ahead. Nothing here installs Playwright/Chromium or modifies stable
skills, `safety_gate`, or `promotion_policy` — those are environment/operator
actions, not code changes in this repo.

## Sequence

1. **Run the open_localhost_browser_v1 real-browser gate** in an environment that
   has Playwright + Chromium installed
   (`pip install playwright && playwright install chromium`). Execute the checks
   in `harnesses/candidates/open_localhost_browser_v1/playwright_verification_plan.md`:
   real-browser smoke (`browser_mode=playwright`), JS-rendered content, screenshot,
   graceful-fail-when-missing, and an e2e at 1.0 with `is_real_browser=true`.

2. **If the gate passes → mark `open_localhost_browser_v1` staging-ready.** Flip
   its candidate stage and record `engine=playwright` / `is_real_browser=true`
   from the verification run. (Until then it stays `dev`;
   **http_fallback is not a real browser**.)

3. **Start `read_browser_console_v1`.** Only after step 2. It is **blocked** until
   a real browser exists, because a console on the http_fallback would be fake.

4. **`read_browser_console_v1` must force `browser_mode=playwright`.** It must
   require a real browser runtime and fail with `browser_runtime_missing` when
   Playwright is absent — never degrade to a fabricated console.

5. **Build `full_browser_vite_login_bug_e2e`** — the end-to-end chain on the real
   browser:
   - `start_local_server` (keep_alive)
   - → `open_localhost_browser` (real browser)
   - → `read_browser_console`
   - → `patch_file_and_run_tests`
   - → rerun + verify
   The orchestrator tears down the kept-alive server at the end of the run.

## Parallel, non-blocking items

- Human shell-execution review sign-off for `patch_file_and_run_tests_v2`
  (unblocks its move to `staging`) and for `start_local_server_v1.2`.
- Decide whether an OS-level guard (cgroup/systemd-scope or supervised reaper) is
  needed for `start_local_server` kept-alive servers — the current lease is
  advisory, not an OS-level watchdog.

## Explicitly out of scope right now

- Do not start `read_browser_console` (blocked).
- Do not add a scheduled reaper / cron / loop.
- Do not install Playwright/Chromium as part of this repo.
- Do not modify stable skills, `safety_gate`, or `promotion_policy`.
