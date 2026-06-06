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

## 4. read_browser_console_v1 — **dev (real browser only)**

- **Started** (the Playwright gate passed). `read_browser_console_v1` is a real
  Playwright console collector — `dev`.
- **Forces `browser_mode=playwright`. `http_fallback` is rejected**
  (`http_fallback_not_allowed`); a missing runtime fails with
  `browser_runtime_missing`. It **never** produces a fake console (ADR-013).
- Evidence: `read_browser_console_smoke` scores 1.0 in a Playwright environment
  (`engine=playwright`, `is_real_browser=true`, `console_supported=true`, correct
  console counts).
- Verdict: keep `dev`. Before staging: wire it into the full browser e2e and pass
  that chain; promotion needs human review (browser runtime).

## 5. full_browser_vite_login_bug_e2e — **executable gate, PASSING**

- The full real-browser e2e is **wired and executable** and **passes 1.0** via
  `scripts/run_full_browser_gate.py` in a Playwright environment (all four
  prerequisites met): start_local_server (keep_alive) → open (real browser) →
  read console (pre-patch error collected) → patch + tests → re-open (real
  browser) → read console (post-patch fatal=0) → orchestrator teardown.
- Evidence: `docs/checkpoints/phase_1b_full_browser_gate_passed.md`.
- This is now the **real-browser promotion bar**. **http_fallback is not a real
  browser** and can never satisfy it. No candidate is promoted to `stable` by this
  review.

## Cross-cutting gate

No candidate may reach `stable` in this review. Two human gates remain open:
shell-execution review (patch runner, start_local_server) and the Playwright
real-browser gate (open_localhost_browser → read_browser_console → full browser
e2e). **http_fallback is not a real browser**, so it can never satisfy any of
these.
