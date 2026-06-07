# 06 — Evaluation and Results

All results below are reproducible from the repo. Real-browser results use the project
`.venv` (Playwright + Chromium); `--dry-run` forms are safe anywhere.

## Results table

| Check | Command | Result |
|---|---|---|
| Project structure | `python scripts/validate_structure.py` | PASS |
| Workflows + all sub-validators | `python scripts/validate_workflows.py` | PASS |
| Secret hygiene | `python scripts/check_secret_hygiene.py` | PASS (exit 0) |
| Config (no secret; provider consistent) | `python scripts/validate_config.py` | PASS |
| Fake provider smoke | `python scripts/llm_smoke.py --fake-only` | provider = fake |
| Unit tests | `python scripts/run_unit_tests.py` | **453/453** passed |
| Skill tests | `python scripts/run_skill_tests.py` | PASS (5 skills) |
| Vertical-slice demo | `python scripts/run_demo.py --demo vite_login_bug` | **1.0** |
| Real-browser e2e | `python scripts/run_full_browser_gate.py` (.venv) | **1.0** |
| Planner execution (real browser) | `evals/planner/fake_full_browser_plan_execution.yaml` (.venv) | **1.0** |
| Repair proposal | `evals/repair/fake_repair_proposal_only.yaml` | **1.0** |
| Approved patch application | `evals/repair/fake_approved_patch_application.yaml` | **1.0** |
| Candidate merge | `evals/repair/fake_candidate_merge.yaml` | **1.0** |
| Staging promotion | `evals/repair/fake_staging_promotion.yaml` | **1.0** |
| Dashboard read-only smoke | `python scripts/run_dashboard_smoke.py` (.venv) | **1.0** |
| Stable promotion readiness | `reports/stable_promotion_readiness_audit_v0/` | **NO-GO / BLOCKED** |

## Notes on the numbers

- **Unit tests 453/453** include per-phase, per-story, and doc-lock tests that freeze
  each capability's boundaries (read-only dashboard, no-secret, no-action, etc.).
- **Real-browser metrics** require Playwright/Chromium; under the system interpreter
  the browser/console steps degrade gracefully (e.g. planner-exec scores 0.9091
  without a real browser). **http_fallback is not a real browser.**
- **Dashboard smoke (1.0)** asserts the UI is read-only at load: no button/form/
  onclick/POST, only `127.0.0.1` requests, no secret in body, and no lingering
  process after teardown.
- **Stable promotion** is intentionally **not** a 1.0 result — the audit concludes
  **NO-GO / BLOCKED** because the human gates are unmet (this is the correct, safe
  outcome, not a failure).

## Evaluation method

Each capability shipped with its own `evals/` task (success_criteria) run via
`scripts/run_eval.py`, plus unit tests. Every artifact is redacted; runs are
gitignored. Gates are wired into `validate_workflows.py` so regressions are caught
centrally.
