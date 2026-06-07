# OpenAI Multi-Step Plan Review v0

Has the OpenAI live planner produce a fixed-goal, **two-step** read-only plan
(`inspect_project` → `list_project_files`) and emits a **human-review package** — and
nothing else. It is **plan-review only**: the plan is **never executed**, **never
auto-repaired**, and no repair / apply / merge / staging / promotion is started. It
never adds the plan to an approved fixture.

Script: [`../../scripts/openai_multistep_plan_review.py`](../../scripts/openai_multistep_plan_review.py).
Eval: [`../../evals/planner/openai_multistep_plan_review.yaml`](../../evals/planner/openai_multistep_plan_review.yaml)
(category `planner_multistep_review`, score **1.0**).

## Fixed goal (no arbitrary prompt)

```
Create a safe read-only two-step project inspection plan:
1. inspect_project
2. list_project_files
Do not execute anything.
```

## What the package contains (all redacted)

| File | Purpose |
| --- | --- |
| `plan.json` | the validated, redacted two-step plan |
| `plan_summary.md` | a redacted human summary |
| `risk_assessment.md` | per-step + overall risk (BLOCKED if any step is not low-risk or non-allowlisted) |
| `approval_checklist.md` | **NOT APPROVED BY DEFAULT** (`APPROVED_FOR_READONLY_EXECUTION: false`) |
| `execution_preconditions.md` | what a later read-only execution must satisfy |
| `review_report.json` | machine summary incl. `multistep_plan_detected`, `inspect_project_present`, `list_project_files_present`, `low_risk_only`, `plan_not_executed` |

Live packages write under the gitignored `runs/openai_multistep_plan_review/`.

## How to use

```bash
# Offline, deterministic (default) — two-step plan, no API call:
.venv/bin/python scripts/openai_multistep_plan_review.py --dry-run

# Operator opt-in: ONE real OpenAI two-step plan, then review it (needs the OpenAI key):
.venv/bin/python scripts/openai_multistep_plan_review.py --real-call

# Re-runnable, CI-safe eval (no API call):
.venv/bin/python scripts/run_eval.py --task evals/planner/openai_multistep_plan_review.yaml   # → 1.0
```

## Safety boundaries

- **Dry-run by default; no API call.** A real call needs `--real-call` + provider=openai
  + `allow_real_api_calls=true` + the OpenAI key present in `os.environ` (read only at
  call time; never `.env` / `password_and_api.txt` / config; key never printed/committed).
- The model must return a JSON plan that passes `PlanValidator`, contains **only**
  `inspect_project` + `list_project_files`, is multi-step, and is all low-risk —
  otherwise a **BLOCKED** package is produced (no auto-fix).
- **Approval stays NOT APPROVED**; `plan_executed` is always false; the plan is never
  added to an approved fixture. Approving and executing remain separate, human-gated
  steps via `scripts/run_openai_readonly_execution_gate.py` /
  `scripts/execute_openai_readonly_plan.py`.
- Plan-review only: no execution, no auto-repair, no repair/apply/merge/staging/
  promotion. The read-only allowlist is unchanged. Stable skills / active candidate /
  `safety_gate` / `promotion_policy` are untouched.
