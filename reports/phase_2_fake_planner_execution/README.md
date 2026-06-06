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

## Results

- `evals/planner/fake_patch_plan_execution.yaml` → **1.0** under the system
  interpreter (inspect → patch → tests pass; no browser needed).
- `evals/planner/fake_full_browser_plan_execution.yaml` → **1.0** via the
  real-browser gate (`python scripts/run_full_browser_gate.py`) — the SAME chain
  as `full_browser_vite_login_bug_e2e` (server → open/console pre → patch →
  re-open/console post), driven entirely by a fake plan through the bridge, with
  no lingering process.
- `scripts/execute_plan.py` — default `--dry-run` (prints the sequence, runs
  nothing); `--execute` runs an allowlisted patch-only plan to 1.0; unknown /
  unvalidated / no-context plans exit non-zero (fail closed).

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
