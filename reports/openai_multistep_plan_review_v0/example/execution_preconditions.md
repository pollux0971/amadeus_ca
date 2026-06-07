# Execution Preconditions (read-only)

A later read-only execution of this plan is permitted ONLY when ALL hold:

1. The plan passes PlanValidator (`plan_valid: true`).
2. review_status is REVIEW-READY (overall_risk = low; no blocked reasons).
3. Every step's skill is in the read-only allowlist (v0: `inspect_project`).
4. approval_checklist.md has `APPROVED_FOR_READONLY_EXECUTION: true` and a non-empty `reviewer:`.
5. Execution is dry-run by default; a real run needs an explicit `--approved` flag plus a non-empty `--reviewer`.
6. Execution context (e.g. the project_dir) comes from a vetted operator input — NEVER from the model's plan inputs, browser content, or run traces.
7. No patch / repair / apply / merge / staging / promotion / server / browser / raw-shell step is present or executed.

> Current review_status: REVIEW-READY. Approval is NOT granted in this package.
