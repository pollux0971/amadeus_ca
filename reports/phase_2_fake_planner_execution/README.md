# Phase 2 — Fake Planner Execution Bridge

This phase adds a **controlled, allowlisted execution bridge** so a *validated*
fake-planner plan can be run by the existing orchestrator. It builds on Phase 1
(real-browser e2e) and the Fake LLM Planner v1 (plan-only).

## Purpose

Close the gap between "a plan exists" and "skills run" — **safely**. The bridge is
the gate that decides whether a plan may execute, and turns it into the exact
aliased skill sequence the existing chains already use.

## What it is NOT (hard limits)

- **Not a general autonomous agent.** It maps one validated plan to one sequence
  and runs it. **No replan, no retry, no auto-repair loop.**
- **No real API call, no env-var key read, no OpenAI/Anthropic provider** — the
  planner stays fake-only.
- **No direct shell.** Only allowlisted, registered skills run; shell only ever
  happens *inside* a vetted skill. The planner never supplies a command.
- **No Safety Gate change, no stable-skill / promotion-policy change.**

## Guarantees

| Guarantee | Mechanism |
| --- | --- |
| Only a validated plan executes | bridge re-checks `PlanValidationResult.valid`; fail closed |
| Allowlisted skills only | `inspect_project`, `start_local_server`, `open_localhost_browser`, `read_browser_console`, `patch_file_and_run_tests` |
| Direct shell rejected | denylist + validator (`raw_shell`/`eval`/`exec`/… rejected) |
| High-risk needs approval | `requires_approval` + `--approve-high-risk`, else fail closed |
| No secret in artifacts | `plan.json` / `plan_execution_trace.jsonl` / `plan_execution_summary.md` / `score.json` / `task.yaml` all redacted; goal redacted at the door |
| Execution context is vetted | fixed per-marker registry, NOT planner output |

## The full chain

```
FakeLLMProvider  →  FakePlanner  →  PlanValidator  →  ExecutionBridge
   (offline,         (marker →        (ids/deps/        (allowlist +
    deterministic)    Plan)            risk/secret)      approval; alias map)
        →  Orchestrator (category: planner_execution; Safety Gate per command)
        →  SkillExecutor  →  Browser / CLI / Patch skills  →  Evaluator
```

See `03_architecture_diagram_planner_execution.md` for the diagram and
`02_demo_script_planner_execution.md` for a runnable walk-through.

## Results

| Eval | Category | Score | Where |
|---|---|---|---|
| `fake_full_browser_plan` | planner (plan-only) | **1.0** | system interpreter |
| `fake_patch_plan_execution` | planner_execution | **1.0** | system interpreter |
| `fake_full_browser_plan_execution` | planner_execution | **1.0** | real browser via `scripts/run_full_browser_gate.py` (.venv) |
| `full_browser_vite_login_bug_e2e` | browser | **1.0** (still) | real browser via the gate (.venv) |

- `evals/planner/fake_patch_plan_execution.yaml` → **1.0** under the system
  interpreter (inspect → patch → tests pass; no browser needed).
- `evals/planner/fake_full_browser_plan_execution.yaml` → **1.0** via the
  real-browser gate — the SAME chain as `full_browser_vite_login_bug_e2e` (server
  → open/console pre → patch → re-open/console post), driven entirely by a fake
  plan through the bridge, with no lingering process.
- `scripts/execute_plan.py` — default `--dry-run` (prints the sequence, runs
  nothing); `--execute` runs an allowlisted patch-only plan to 1.0; unknown /
  unvalidated / no-context plans exit non-zero (fail closed).

## Remaining risks

- **No real API.** Fake provider only; the real provider is intentionally not
  implemented (loader fails closed).
- **No auto-repair.** There is no failure → repair loop yet (a separate, gated
  phase).
- **No autonomous replan.** The bridge maps a plan once and runs it — no retry,
  no re-plan.
- **Plan markers are still deterministic, not semantic planning.** `FakePlanner`
  selects a fixed plan per marker; it does not reason about an arbitrary goal.
- **Stable promotion still requires human review.** Passing the planner-execution
  and real-browser gates is NOT a stable promotion; shell-executing candidates
  need a human shell-execution + policy review first.

## Key files

- `src/planner/execution_bridge.py` — `build_execution_sequence`,
  `execution_context_for`, allowlist + approval policy.
- `scripts/execute_plan.py` — CLI (dry-run default, `--execute`,
  `--approve-high-risk`).
- `src/orchestrator/orchestrator.py` — `category: planner_execution` branch (the
  plan-only `planner` category is unchanged).
- `specs/planner/plan_execution_bridge_contract.md` — the contract.

## Next (not started)

Auto-repair loop is intentionally **not** started: re-planning on failure is the
next gated phase, separate from this one.
