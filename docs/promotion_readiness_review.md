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

## 6. Full real-browser e2e — **PASSED (integration gate)**

- `full_browser_vite_login_bug_e2e` **passes 1.0** end to end on a real Playwright
  browser (start → open → console pre → patch + tests → re-open → console post →
  fatal=0). Evidence:
  `docs/checkpoints/checkpoint-phase-1b-full-browser-e2e.md`.
- **This means the integration gate is met — it is NOT a stable promotion.**
  **Stable promotion still needs review:** shell-executing candidates (patch
  runner, start_local_server) require a human shell-execution review, and the
  promotion policy review must sign off before any `stable` move.

## 7. Fake planner execution bridge — **PASSED (gate), NOT a promotion**

- The fake planner execution bridge is green: a *validated* fake plan is executed
  through an **allowlisted** bridge (`fake_patch_plan_execution` 1.0;
  `fake_full_browser_plan_execution` 1.0 on a real browser). It runs only
  allowlisted skills, no direct shell, no unapproved high-risk step, and **no
  autonomous replan**. Evidence:
  `docs/checkpoints/checkpoint-phase-2a-fake-planner-execution.md`.
- **This does NOT mean auto-repair may be enabled.** Passing the execution-bridge
  gate is not authorization to re-plan or self-modify. The **auto-repair loop is
  not started** and is blocked behind a new gate (repair-proposal only, candidate
  workspace, approval gate; never modifies stable directly).
- **Stable promotion still needs review.** The execution bridge changes nothing
  about the stable-promotion bar: shell-executing candidates still require a human
  shell-execution review and the promotion-policy review before any `stable` move.

## 8. Auto Repair Loop v0 (proposal-only) — **PASSED (gate), NOT an apply mandate**

- The repair loop is green at v0: a failed eval becomes a validated, redacted
  repair *proposal* in a candidate workspace (`fake_repair_proposal_only` 1.0).
  It applies nothing, modifies no candidate/stable code, and promotes nothing.
  Evidence: `docs/checkpoints/checkpoint-phase-3-repair-proposal-only.md`.
- **This does NOT authorize automatic apply.** Passing the proposal gate is not a
  mandate to apply a proposal. Apply is a separate, human-approved phase — now
  implemented at v0 as **workspace-only** (`scripts/repair_apply.py`, see section
  9); `repair_propose.py --apply` remains rejected. Apply still touches no stable
  code and promotes nothing.
- **Stable promotion still needs review** — unchanged: shell-executing candidates
  require a human shell-execution review and the promotion-policy review before any
  `stable` move.

## 9. Approved Patch Application v0 (workspace-only) — **PASSED (gate), NOT a merge mandate**

- Approved patch application is green at v0: a human-approved proposal is
  materialized into an apply workspace (`fake_approved_patch_application` 1.0). It
  writes no real target file, modifies no candidate/stable code, and promotes
  nothing. Evidence: `docs/checkpoints/checkpoint-phase-4-approved-patch-application.md`.
- **This does NOT authorize automatic merge or promotion.** Passing the apply gate
  is not a mandate to merge an apply workspace. **Merge and promotion are not
  started.** Merging is a separate, human-driven phase: review the apply workspace,
  merge into a **candidate** (never stable directly), run targeted tests +
  regression, produce a rollback plan, then the promotion policy applies.
- **Stable promotion still needs review** — unchanged: shell-executing candidates
  require a human shell-execution review and the promotion-policy review (and now a
  rollback plan) before any `stable` move.

## 10. Candidate Merge v0 (candidate-workspace-only) — **PASSED (gate), NOT a promotion mandate**

- Candidate merge is green at v0: a human-approved apply workspace is merged into a
  candidate merge workspace with a rollback plan + promotion review package
  (`fake_candidate_merge` 1.0). It writes no real target file, modifies no active
  candidate or stable code, and promotes nothing. Evidence:
  `docs/checkpoints/checkpoint-phase-5-candidate-merge.md`.
- **This does NOT authorize automatic staging/stable promotion.** Passing the merge
  gate is not a mandate to promote. **Promotion is not started.** Staging promotion
  is a separate, human-driven phase: review the merge workspace, **verify the
  rollback plan**, run targeted tests + regression, then the promotion policy moves
  a candidate toward `staging`; stable promotion needs a further policy review.
- **Stable promotion still needs review** — unchanged: a human shell-execution
  review, the promotion-policy review, and rollback verification before any `stable`
  move.

## 11. Staging Promotion v0 (staging-workspace-only) — **PASSED (gate), NOT a stable mandate**

- Staging promotion is green at v0: a human-approved candidate merge workspace is
  promoted into a staging workspace with verified rollback + recorded regression +
  a stable-promotion checklist (`fake_staging_promotion` 1.0). It writes no real
  target file, modifies no active candidate or stable code, and stable-promotes
  nothing. Evidence: `docs/checkpoints/checkpoint-phase-5-candidate-merge.md` (Phase
  5) and the staging contract `specs/repair/staging_promotion_contract.md`.
- **This does NOT authorize automatic stable promotion.** Reaching staging is not a
  mandate to promote to `stable`. **Stable promotion is not started.** Stable
  promotion is a separate, human-driven phase: review the staging workspace, confirm
  the verified rollback + full regression, complete the human shell-execution
  review, then the promotion policy moves a candidate to `stable`.
- **Stable promotion still needs review** — unchanged: a human shell-execution
  review, the promotion-policy review, and confirmed rollback before any `stable`
  move.

## Cross-cutting gate

No candidate is promoted to `stable` by this review. The integration (real
browser) gate is passed, but the human shell-execution review and the policy
review remain open before `stable`. **http_fallback is not a real browser**, so it
can never satisfy the real-browser gate. Passing the planner-execution bridge, the
repair-proposal gate, the approved-apply gate, the candidate-merge gate, or the
staging-promotion gate is **not** a stable promotion and does **not** authorize
auto-repair, auto-apply, auto-merge, auto-staging, or auto-promotion. **Stable
promotion is not started.**
