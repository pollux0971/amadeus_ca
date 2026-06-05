# Promotion Readiness Review

Per-candidate promotion verdicts against `specs/harness/promotion_policy.md`.
This review changes no stable skill manifest, `safety_gate`, or
`promotion_policy`. See `docs/candidate_status_matrix.md` for the one-line
summary and `harnesses/candidates/<id>/candidate_summary.md` for details.

## 1. patch_file_and_run_tests_v2 — **staging-ready (after human shell review)**

- **Can go to staging.** Required checks pass: candidate + harness unit tests,
  integration evals (`vite_login_bug` 1.0, `py_calc_bug_e2e` 1.0), sandboxed
  patching, no secret access, no destructive command.
- **Before `stable`: a human shell-execution review sign-off is still required.**
  The runner executes a `test_command` through the Safety Gate; per
  `promotion_policy.md` ("modifies shell execution") this needs human review.
  The surface is documented in its `human_shell_review.md` (reviewer box).
- Verdict: promote to `staging` on the human sign-off; **do not promote to
  `stable`** as part of this review.

## 2. start_local_server_v1.2 — **hold at dev / staging-candidate**

- May remain `dev` (a staging-candidate). It is real: subprocess lifecycle,
  keep-alive handoff, idempotent teardown, and a **lease reaper** already exist.
- Remaining risk: the lease is **advisory — it is not an OS-level watchdog**.
  Cleanup depends on the orchestrator's end-of-run teardown, an explicit
  `teardown`, or running the reaper CLI. Between a crash and the next reaper run
  a stale server can live up to `lease_ttl_sec`.
- Also executes shell commands → a human shell review is required before staging,
  and a real keep-alive **consumer** (a real browser) is still pending.
- Verdict: keep `dev`/staging-candidate; not staging until the shell review and
  the OS-level-guard question are settled.

## 3. open_localhost_browser_v1 — **keep dev (blocked from staging)**

- **HTTP fallback only counts as a localhost smoke.** This environment has no
  Playwright/Chromium, so the e2e (`open_localhost_keep_alive_smoke` 1.0) runs on
  the **http_fallback** engine. **http_fallback is not a real browser** — no JS,
  no rendered DOM, no console, no screenshot.
- The 1.0 is honestly marked: every result and the score metrics carry
  `engine=http_fallback`, `is_real_browser=false` (ADR-013).
- **Must NOT go to staging before the real Playwright browser e2e passes** (see
  `harnesses/candidates/open_localhost_browser_v1/playwright_verification_plan.md`).
- Verdict: stay `dev` until the Playwright gate is green.

## 4. read_browser_console — **blocked**

- **Blocked. Must depend on `browser_mode=playwright`** (a real browser with a
  real console).
- **http_fallback must not be used to produce a fake console.** A console skill on
  the fallback would emit an empty/fabricated console and silently corrupt every
  downstream evaluation (ADR-013).
- Do not start `read_browser_console` until `open_localhost_browser_v1` passes the
  Playwright gate and a real browser runtime is available.
- Verdict: blocked; not started.

## Cross-cutting gate

No candidate may reach `stable` in this review. Two human gates remain open:
shell-execution review (patch runner, start_local_server) and the Playwright
real-browser gate (open_localhost_browser → read_browser_console).
