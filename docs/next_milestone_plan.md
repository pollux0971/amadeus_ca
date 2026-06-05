# Next Milestone Plan

> **Quick resume pointer:** for a one-minute "where am I" summary (active
> overrides, what's green, what's blocked, dry-run commands, next real step), read
> [`docs/quick_resume.md`](quick_resume.md). The ordering below is unchanged.

Ordered plan after the candidate-status review. Each step has an explicit gate;
do not skip ahead. Nothing here installs Playwright/Chromium or modifies stable
skills, `safety_gate`, or `promotion_policy` — those are environment/operator
actions, not code changes in this repo.

## Sequence

1. **Run the open_localhost_browser_v1 real-browser gate** in an environment that
   has Playwright + Chromium installed
   (`pip install playwright && playwright install chromium`). The gate is already
   scaffolded; run it with:

   ```bash
   python scripts/run_playwright_gate.py --dry-run   # safe anywhere: shows the checks/plan
   python scripts/run_playwright_gate.py             # only with Playwright + Chromium
   ```

   The runner checks the Playwright package and a Chromium runtime first (exit
   code 2 and a clear message if either is missing — it never installs anything),
   then runs `evals/browser/open_localhost_playwright_required_smoke.yaml`. That
   eval verifies the checks in
   `harnesses/candidates/open_localhost_browser_v1/playwright_verification_plan.md`:
   `engine=playwright`, `is_real_browser=true`, JS/console/screenshot supported, a
   screenshot artifact, and no lingering server.

   **Status: the gate eval and runner exist, but have NOT been executed in a
   Playwright environment yet** (this sandbox has none). Until
   `python scripts/run_playwright_gate.py` returns PASS (score 1.0,
   `is_real_browser=true`), the gate is not satisfied.

2. **Only after the gate passes → mark `open_localhost_browser_v1` staging-ready.**
   Flip its candidate stage and record `engine=playwright` / `is_real_browser=true`
   from the verification run. (Until then it stays `dev`;
   **http_fallback is not a real browser**.)

3. **Start `read_browser_console_v1`.** Only after step 2. It is **blocked** until
   a real browser exists, because a console on the http_fallback would be fake.

4. **`read_browser_console_v1` must force `browser_mode=playwright`.** It must
   require a real browser runtime and fail with `browser_runtime_missing` when
   Playwright is absent — never degrade to a fabricated console.

5. **Run `full_browser_vite_login_bug_e2e`** — the end-to-end chain on the real
   browser:
   - `start_local_server` (keep_alive)
   - → `open_localhost_browser` (real browser)
   - → `read_browser_console`
   - → `patch_file_and_run_tests`
   - → rerun + verify
   The orchestrator tears down the kept-alive server at the end of the run.

   The gate is already scaffolded (a **draft** eval + a runner); run it with:

   ```bash
   python scripts/run_full_browser_gate.py --dry-run   # safe anywhere: lists blocked prerequisites
   python scripts/run_full_browser_gate.py             # only when ALL prerequisites are met
   ```

   `run_full_browser_gate.py` refuses to run (exit code 2) until **all** of:
   (a) the Playwright package, (b) a Chromium runtime, (c) the
   `open_localhost_browser` real-browser gate has **passed**, and (d) a
   `read_browser_console` candidate **exists**. It installs nothing.

   **Status: the full-browser gate eval (`draft: true`,
   `blocked_until: playwright_gate_passed_and_console_skill_exists`) and its runner
   exist, but the gate is NOT yet runnable** — both the real-browser Playwright
   gate (step 1) and `read_browser_console_v1` (steps 3–4) must come first. This
   does **not** change the order: `read_browser_console` still cannot start early.

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
