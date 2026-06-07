# 02 — Gate Results

Two classes of gate: **engineering gates** (automated, currently green) and **human
gates** (required by the promotion policy, currently **not satisfied**). Stable
promotion needs BOTH.

## Engineering gates (automated)

| Gate | Status | Evidence |
|---|---|---|
| structure | ✅ PASS | `validate_structure.py` |
| workflows / all doc+sub-validators | ✅ PASS | `validate_workflows.py` |
| secret hygiene | ✅ PASS (exit 0) | `check_secret_hygiene.py` |
| config (no secret; provider consistent) | ✅ PASS | `validate_config.py` |
| fake provider smoke | ✅ fake | `llm_smoke.py --fake-only` |
| vertical-slice demo | ✅ 1.0 | `run_demo.py --demo vite_login_bug` |
| real-browser e2e | ✅ 1.0 (.venv) | `run_full_browser_gate.py` |
| dashboard read-only smoke | ✅ 1.0 (.venv) | `run_dashboard_smoke.py` |
| repair chain evals | ✅ 1.0 | proposal / approved-apply / candidate-merge / staging |
| unit tests | ✅ all pass | `run_unit_tests.py` |

## Rollback verification status

- **Workspace-level rollback present** (Phase 5 `rollback_plan.md`, Phase 6
  `rollback_verification.md`). These cover *workspace* reversibility (delete the
  workspace).
- **Stable-deployment rollback: NOT verified by a human.** A stable promotion needs a
  stronger, deployed-state rollback that a human has reviewed and confirmed. **Status:
  NOT SATISFIED.**

## Full regression status

- The fixed test allowlist (validate_structure / validate_workflows / unit tests /
  vite demo / repair+planner evals) is recorded by the staging gate and is green here.
- **A human-signed full-regression run for a stable cut: NOT recorded. Status: NOT
  SATISFIED** (no human attestation that the regression suite was run and reviewed for
  a stable promotion).

## Human gates (required by the promotion policy)

| Human gate | Status |
|---|---|
| Human shell-execution review sign-off (shell-executing candidates) | ❌ **NOT SATISFIED** |
| Promotion-policy review sign-off | ❌ **NOT SATISFIED** |
| Explicit operator approval to promote to stable | ❌ **NOT SATISFIED** |
| Rollback-verification review (deployed-state) | ❌ **NOT SATISFIED** |
| Human approval marker captured for stable | ❌ **NOT SATISFIED** |

## Summary

Engineering gates: **green**. Human gates: **not satisfied**. Per the Go/No-Go rule,
any missing human gate forces **NO-GO / BLOCKED**.
