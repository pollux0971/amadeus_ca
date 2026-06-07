# Approved Review Package Import v0

A safe flow that turns an OpenAI (multi-step) **review package** into a **NOT-APPROVED
fixture candidate** for human review. It is **import / validation / approval-checklist
only**: it NEVER auto-approves, NEVER executes a plan, and NEVER does repair / apply /
merge / staging / promotion.

Script: [`../../scripts/import_review_package.py`](../../scripts/import_review_package.py).
Eval: [`../../evals/planner/review_package_import.yaml`](../../evals/planner/review_package_import.yaml)
(category `review_package_import`, score **1.0**).

## What it does

```bash
# Validate only (default) — writes nothing:
.venv/bin/python scripts/import_review_package.py --dry-run \
    --review-package reports/openai_multistep_plan_review_v0/example

# Materialize a NOT-APPROVED fixture candidate (operator opt-in):
.venv/bin/python scripts/import_review_package.py --write \
    --review-package reports/openai_multistep_plan_review_v0/example
```

The candidate is written to
`fixtures/openai_planner/imported_review_package_<id>/` (gitignored — operator
output, never committed) and contains: `plan.json`, `plan_summary.md`,
`approval_checklist.md`, `import_report.json`, `README.md` — all redacted.

## Hard boundaries

- **Dry-run by default; `--write` required to create anything.**
- **NEVER auto-approves.** The generated `approval_checklist.md` is always
  `APPROVED_FOR_READONLY_EXECUTION: false`. The import tool never writes the approved
  marker; granting approval stays a separate, human, manual edit.
- **The plan must pass `PlanValidator`, use ONLY `inspect_project` +
  `list_project_files`, and be all low-risk** — else the import is BLOCKED (no
  auto-fix). The read-only allowlist is **unchanged**.
- **No plan execution, no OpenAI / network call, no `.env` / password-file read.** All
  artifacts redacted.
- **Approval parsing is line-anchored.** The execution gate
  (`src/planner/read_only_execution_gate.py`) now grants approval ONLY from a
  standalone `APPROVED_FOR_READONLY_EXECUTION: true` LINE, so a NOT-APPROVED checklist
  whose help text mentions the marker can never be mis-read as approved.
- Stable skills / active candidate / `safety_gate` / `promotion_policy` are untouched.

## Where it fits

```
OpenAI multistep plan review (NOT APPROVED package)
  -> import_review_package (NOT APPROVED fixture candidate)     <-- this story
  -> [human edits APPROVED_FOR_READONLY_EXECUTION: true + reviewer]
  -> run_openai_readonly_execution_gate / execute_openai_readonly_plan (read-only run)
```
