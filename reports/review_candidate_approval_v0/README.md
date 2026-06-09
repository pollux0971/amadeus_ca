# Review Package Approval Helper v0

A **human-approval** helper that materializes a NOT-APPROVED imported review candidate
into an **approved** read-only fixture the execution gate can run. It is
approval-materialization only: it NEVER executes a plan, NEVER calls OpenAI, and NEVER
does repair / apply / merge / staging / promotion.

Script: [`../../scripts/approve_review_candidate.py`](../../scripts/approve_review_candidate.py).
Eval: [`../../evals/planner/review_candidate_approval.yaml`](../../evals/planner/review_candidate_approval.yaml)
(category `review_candidate_approval`, score **1.0**).

## What it does

```bash
# Validate only (default) — writes nothing:
.venv/bin/python scripts/approve_review_candidate.py --dry-run \
    --candidate reports/openai_multistep_plan_review_v0/example --output-id smoke

# Materialize an APPROVED fixture (requires --approve + a real --reviewer):
.venv/bin/python scripts/approve_review_candidate.py --approve --reviewer "alice" \
    --candidate fixtures/openai_planner/imported_review_package_<id> --output-id myrun
```

The approved fixture is written to
`fixtures/openai_planner/approved_imported_<id>/` (gitignored — operator output, never
committed) and contains `plan.json`, `approval_checklist.md`, `approval_report.json`,
`README.md` — all redacted.

## Hard boundaries

- **Dry-run by default; `--approve` required to write.**
- **A real run requires a non-empty `--reviewer`** that is not a placeholder
  (TBD / TODO / unknown / none). The approval is granted by the named human, not by the
  model or the planner.
- **The source candidate must be NOT APPROVED already** and must be an
  `imported_review_package_*` dir under `fixtures/openai_planner/` OR a committed
  example review package. The tool never re-approves an already-approved fixture and
  never approves an arbitrary path.
- **The plan must pass `PlanValidator`, use ONLY `inspect_project` +
  `list_project_files`, and be all low-risk** — else BLOCKED. The read-only allowlist
  is **unchanged**.
- **The approval marker is a standalone, line-anchored line**
  `APPROVED_FOR_READONLY_EXECUTION: true`, recognized by the gate's line-anchored
  `parse_approval` (help text mentioning the marker can never grant approval).
- **No plan execution, no OpenAI / network call, no `.env` / password-file read.** All
  artifacts redacted.
- Stable skills / active candidate / `safety_gate` / `promotion_policy` are untouched.

## Where it fits

```
OpenAI multistep plan review (NOT APPROVED package)
  -> import_review_package (NOT APPROVED fixture candidate)
  -> approve_review_candidate (APPROVED fixture, named human reviewer)   <-- this story
  -> run_openai_readonly_execution_gate / execute_openai_readonly_plan (read-only run)
```
