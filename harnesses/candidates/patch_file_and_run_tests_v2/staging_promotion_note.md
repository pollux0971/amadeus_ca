# Staging Promotion Note — patch_file_and_run_tests_v2

## Decision

`patch_file_and_run_tests_v2` is marked **staging-ready** (`candidate.yaml`
`status: staging-ready`). It is **not** promoted to `stable`. The actual move to
`staging` is gated on a human sign-off in `human_shell_review.md`.

## Why it is ready

Against `promotion_policy.md`:

| Required check | Status |
|---|---|
| unit_tests_pass | 52/52 PASS |
| integration_tests_pass | vite_login_bug 1.0, py_calc_bug_e2e 1.0 (full orchestrator) |
| security_tests_pass | blocked-command + sandbox + no-mutation tests pass |
| no_secret_leak | v2 reads no secrets / `.env`; no network calls |
| no_destructive_command | only shell path is the Safety-Gated `run_command` |

Metric gates (`promotion_policy.md`):

| Metric | Gate | Observed |
|---|---|---|
| success_rate_delta_min | ≥ 0.00 | vite stayed 1.0; py_calc_bug_e2e new at 1.0 |
| regression_tolerance | 0.00 | candidates-disabled regressions unchanged (vite 0.667 stable, e2e fails to stable placeholder) |
| flaky_rate_max | ≤ 0.05 | deterministic; sandboxed; no observed flakiness |

"Human review required" trigger that applies: **modifies shell execution** →
addressed by `human_shell_review.md` (surface documented; awaiting sign-off).

## State changes made in this preparation

- `patch_file_and_run_tests_v2/candidate.yaml`: `status: dev → staging-ready`.
- `patch_file_and_run_tests_v1/candidate.yaml`: `active: true → false`,
  `status: dev → superseded`, `superseded_by: patch_file_and_run_tests_v2`.
  v1 is **retired, not deleted** (kept for history and its tests).
- Active override after retirement (verified):
  `{patch_file_and_run_tests: patch_file_and_run_tests_v2}`.

Not changed (per constraints): stable `skills/` manifests, `safety_gate`,
`promotion_policy`, and the v2 patch-runner logic (no new features).

## Steps to actually promote to staging (post-sign-off)

1. Reviewer ticks "Approve … staging" in `human_shell_review.md`.
2. Set `candidate.yaml` `status: staging` (and record the reviewer/date).
3. Keep v1 `active: false`.
4. Observe in staging per the policy before any separate `stable` decision.

## Explicitly out of scope

- No promotion to `stable`.
- No new patch-runner functionality.
- No changes to `safety_gate` / `promotion_policy` / stable skill manifests.
