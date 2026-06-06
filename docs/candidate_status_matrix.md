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
| `open_localhost_browser_v1` | open_localhost_browser | `true` | 1 | **staging-ready** | candidate + e2e unit tests pass | **real-browser gate `open_localhost_playwright_required_smoke` 1.0** (`engine=playwright`, `is_real_browser=true`) | none for the browser smoke (Playwright gate passed); `read_browser_console` is a separate, still-blocked track | **Staging-ready after real-browser gate.** Promote to `staging` on operator approval; the http_fallback path remains a smoke only (**http_fallback is not a real browser**). |
| `read_browser_console_v1` | read_browser_console | `true` | 1 | **dev** | candidate + e2e unit tests pass | `read_browser_console_smoke` 1.0 (real Playwright browser) | must pass the console smoke before staging-ready (passes in a Playwright env); still to be wired into the full browser e2e | **Real browser only — no `http_fallback`** (`http_fallback_not_allowed`); forces `browser_mode=playwright`. Hold at `dev`; promotion needs human review (browser runtime). A console on `http_fallback` would be fake (ADR-013). |
| `full_browser_vite_login_bug_e2e` | n/a (multi-skill e2e gate) | n/a | — | **passed** | full e2e + evidence unit tests pass | **`full_browser_vite_login_bug_e2e` 1.0 — PASSED** (real browser: start→open→console→patch→re-open→re-console; pre-patch console error collected, post-patch fatal=0) | must keep passing the full gate as the integration bar | **Passed** via `scripts/run_full_browser_gate.py` (Playwright env). Integration gate met; the real-browser path is the bar. **http_fallback is not a real browser**. |

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

## Planner / execution status (Phase 2A)

| Component | Status | Notes |
|---|---|---|
| **FakeLLMProvider** | **completed** | offline, deterministic; no real API, no env-var key read; loader fails closed |
| **FakePlanner v1** | **completed** | marker → deterministic plan; **plan-only** (never executes); `fake_full_browser_plan` 1.0 |
| **PlanValidator** | **completed** | unique ids / deps / risk / **no direct shell** / no secret in inputs |
| **ExecutionBridge v1** | **completed** | only a *validated* plan; **allowlisted skills only**; high-risk needs approval; **no autonomous replan**; `fake_patch_plan_execution` 1.0, `fake_full_browser_plan_execution` 1.0 (real browser) |
| **AutoRepairLoop v0** | **proposal-only completed** | failed eval → failure analysis → fake repair proposal → candidate workspace → human approval gate; `fake_repair_proposal_only` 1.0 |
| **ApprovedPatchApplication v0** | **workspace-only completed** | human-approved proposal → `repair_apply.py` materializes proposed_changes into an apply workspace; `fake_approved_patch_application` 1.0; needs approval marker + reviewer + `--approved`; **no stable change, no merge, no promotion** |
| **CandidateMerge v0** | **candidate-workspace-only completed** | human-approved apply workspace → `repair_merge.py` merges proposed_changes into a candidate merge workspace; `fake_candidate_merge` 1.0; needs merge marker + reviewer + `--approved` + `--reviewer`; produces `rollback_plan.md` + `promotion_review_package.md`; **no active candidate change, no stable change, no promotion** |
| **StagingPromotion v0** | **staging-workspace-only completed** | human-approved candidate merge workspace → `staging_promote.py` promotes merged_changes into a staging workspace; `fake_staging_promotion` 1.0; needs staging marker + reviewer + `--approved` + `--reviewer`; verifies rollback (`rollback_verification.md`), records regression, produces `stable_promotion_checklist.md`; **no active candidate change, no stable change, no stable promotion** |
| **StablePromotion** | **not started / blocked behind policy review** | human review the staging workspace + checklist, confirm verified rollback + full regression, human shell-execution review, promotion policy; **never modifies stable directly** |
| **AutoPromotion** | **not started / forbidden** | promotion stays human-driven under `specs/harness/promotion_policy.md`; nothing is auto-promoted |
| **StableModification** | **forbidden** | no automated phase modifies a stable skill, an active candidate runtime, the safety gate, or the promotion policy |

Frozen at `docs/checkpoints/checkpoint-phase-2a-fake-planner-execution.md`,
`docs/checkpoints/checkpoint-phase-3-repair-proposal-only.md`,
`docs/checkpoints/checkpoint-phase-4-approved-patch-application.md`, and
`docs/checkpoints/checkpoint-phase-5-candidate-merge.md`. The planner-execution,
repair-proposal, approved-apply, candidate-merge, and staging-promotion gates
passing is **not** a stable promotion and does **not** authorize auto-apply,
auto-merge, auto-staging, or auto-promotion.

## Stage legend

- **dev** — experimental; may change.
- **staging-ready** — passed required checks; awaiting the human review the
  promotion policy reserves for shell execution.
- **blocked** — must not proceed until a named prerequisite is met.
- **superseded** — retired in favour of a newer version; kept for history.
