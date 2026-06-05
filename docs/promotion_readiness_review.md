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

## 3. open_localhost_browser_v1 — **staging-ready after the real-browser gate**

- **The Playwright real-browser gate has PASSED.**
  `python scripts/run_playwright_gate.py` ran the eval
  `open_localhost_playwright_required_smoke` to **score 1.0** in a Playwright +
  Chromium environment.
- **Gate artifacts / capability flags (recorded):** `engine=playwright`,
  `is_real_browser=true`, `screenshot_supported=true`, `js_supported=true`,
  `console_supported=true`, a real `screenshot.png` (1280×720) and a
  `page_snapshot.json`, with **no lingering server/browser process**. Evidence:
  `docs/checkpoints/phase_1a_playwright_gate_passed.md` and
  `docs/checkpoints/phase_1a_playwright_environment_setup_report.md`.
- The http_fallback path remains a smoke only — **http_fallback is not a real
  browser** — but the candidate is no longer limited to it.
- Verdict: **staging-ready.** Promote to `staging` on operator approval (the
  browser runtime is reviewed like shell execution); `stable` remains a separate,
  later decision.

## 4. read_browser_console — **blocked**

- **Blocked. Must depend on `browser_mode=playwright`** (a real browser with a
  real console).
- **http_fallback must not be used to produce a fake console.** A console skill on
  the fallback would emit an empty/fabricated console and silently corrupt every
  downstream evaluation (ADR-013).
- Do not start `read_browser_console` until `open_localhost_browser_v1` passes the
  Playwright gate and a real browser runtime is available.
- Verdict: blocked; not started.

## 5. full_browser_vite_login_bug_e2e — **draft, blocked**

- A **full browser e2e gate draft exists, but is blocked until a real browser +
  the console skill exist.** The draft eval
  (`evals/browser/full_browser_vite_login_bug_e2e.yaml`, `draft: true`) and its
  runner (`scripts/run_full_browser_gate.py`) are prepared, but the runner refuses
  to run (exit 2) until the Playwright real-browser gate has passed **and** a
  `read_browser_console` candidate exists.
- This changes **no** candidate's promotion verdict; it only records the future
  end-to-end target and its prerequisites.

## Cross-cutting gate

No candidate may reach `stable` in this review. Two human gates remain open:
shell-execution review (patch runner, start_local_server) and the Playwright
real-browser gate (open_localhost_browser → read_browser_console → full browser
e2e). **http_fallback is not a real browser**, so it can never satisfy any of
these.
