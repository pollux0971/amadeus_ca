# OpenAI Plan Review Package v0

This story (`OpenAI Plan Review Package v0`) turns a planner **plan** into a
**human-review package** — and nothing else. The plan is **never executed**, **never
auto-repaired**, and no repair / apply / merge / staging / promotion is started. It is
the review step between *"the OpenAI planner produced a plan"* and *"a human approves
a controlled, read-only execution"* (the separate Read-Only Plan Execution Gate v0).

Generator: [`../../scripts/openai_plan_review.py`](../../scripts/openai_plan_review.py).

## What the package contains (all artifacts redacted)

| File | Purpose |
| --- | --- |
| `plan.json` | the validated, redacted plan |
| `plan_summary.md` | a redacted human summary of the steps |
| `risk_assessment.md` | per-step + overall risk; **BLOCKED** if any step is not low-risk or uses a non-allowlisted (read-only) skill |
| `approval_checklist.md` | **NOT APPROVED BY DEFAULT / PLAN NOT EXECUTED / HUMAN APPROVAL REQUIRED**, with `APPROVED_FOR_READONLY_EXECUTION: false` |
| `execution_preconditions.md` | the conditions any later read-only execution must satisfy |
| `review_report.json` | machine summary (status, validity, blocked reasons, skills) |

## Review status

- **REVIEW-READY** — the plan passes `PlanValidator`, every step is `risk_level: low`,
  and every step's skill is in the read-only allowlist (v0: `inspect_project`).
- **BLOCKED** — the plan is invalid, or has a non-low-risk step, or uses a
  non-allowlisted skill. A blocked package is still produced (for the record); it is
  **never auto-fixed** and **never executed**.

## How to generate

```bash
# Offline, deterministic (default) — uses a fake inspect plan, no API call:
.venv/bin/python scripts/openai_plan_review.py --dry-run

# Review an existing plan.json (e.g. from scripts/openai_planner_live_plan.py):
.venv/bin/python scripts/openai_plan_review.py --plan-json runs/openai_planner_live_plan/plan.json

# Operator opt-in: ONE real OpenAI plan, then review it (needs OPENAI_API_KEY):
.venv/bin/python scripts/openai_plan_review.py --real-call
```

Live packages are written under the gitignored `runs/openai_plan_review/` by default.

## Committed example

[`example/`](example/) is a committed, deterministic review package built from the
offline fake `inspect_project` plan (`--dry-run`) — no API call, no secret, always
REVIEW-READY. It shows reviewers the exact package shape and is checked by
`tests/unit/test_openai_plan_review.py` and `scripts/validate_workflows.py`.

## Downstream: approved read-only execution + eval gate

The review package feeds the **OpenAI Read-Only Plan Execution Gate v0** and its
**re-runnable eval gate**:

- A human marks `approval_checklist.md` with `APPROVED_FOR_READONLY_EXECUTION: true`
  and a non-empty reviewer (see `fixtures/openai_planner/approved_readonly_plan/`).
- `scripts/execute_openai_readonly_plan.py` runs the approved plan through
  `src/planner/read_only_execution_gate.py`, executing ONLY allowlisted read-only
  skills (v0: `inspect_project`).
- `evals/planner/openai_readonly_execution_gate.yaml` (category
  `planner_readonly_execution`) makes this a **re-runnable eval** scoring **1.0** via
  `scripts/run_eval.py`; `scripts/run_openai_readonly_execution_gate.py` is the
  operator runner (dry-run by default, `--execute` runs the fixture only, no OpenAI
  call, redacted `gate_report.json/.md`).
- **Read-Only Skill Allowlist Expansion v0** added one more safe, content-free skill:
  the allowlist is now **`inspect_project` + `list_project_files`**.
  `list_project_files` lists repo-relative paths + basic metadata only (no file
  contents, `max_files` cap, excludes `.git`/`.venv`/`runs`/`__pycache__`/screenshots/
  `.env`/`config/config.json`/`password_and_api.txt`/secret-looking files, no symlink
  escape). Fixture `fixtures/openai_planner/approved_readonly_plan_list_files/` + eval
  `evals/planner/openai_readonly_list_files_execution_gate.yaml` score **1.0**; the
  runner takes `--fixture inspect_project|list_project_files`. Still no browser /
  server / patch / repair / apply / merge / staging / promotion / raw-shell.
- **OpenAI Read-Only Multi-Step Execution v0** runs an approved plan's allowlisted
  read-only steps **in order** (fixture `approved_readonly_plan_multistep`:
  `inspect_project` → `list_project_files`). The gate records `execution_order`, runs
  each step **once**, and **fails closed on any step failure** (no retry / replan /
  repair). Eval `evals/planner/openai_readonly_multistep_execution_gate.yaml` → 1.0;
  runner `--fixture multistep`. Allowlist unchanged; still no browser / server / patch
  / repair / promotion / raw-shell.

## Safety boundaries

- Fake provider stays the default; a real OpenAI plan needs `--real-call` + a present
  `OPENAI_API_KEY` (read only from `os.environ` at call time; config holds the env-var
  NAME only; the key is never printed/committed).
- Only the FIXED goal `"Create a safe read-only project status inspection plan. Do not
  execute anything."` is ever sent to a real provider — no arbitrary prompt.
- Every artifact is redacted; a secret-looking value never reaches the package.
- Plan-only: no execution, no auto-repair, no repair/apply/merge/staging/promotion.
- Stable skills / active candidate / `safety_gate` / `promotion_policy` are untouched.
