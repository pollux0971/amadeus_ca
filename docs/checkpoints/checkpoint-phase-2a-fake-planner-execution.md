# Checkpoint: Phase 2A — Fake Planner Execution Bridge

- **checkpoint name:** `checkpoint-phase-2a-fake-planner-execution`
- **commit (execution bridge passed):** `f6e71b0`
- **tag:** `checkpoint-phase-2a-fake-planner-execution`

Frozen snapshot of the chain **fake planner → validated plan → allowlisted
execution bridge → full real-browser chain**. Documentation only — no runtime,
candidate, stable skill, safety gate, or promotion policy change.

## What is frozen

- **Fake provider only.** The LLM layer uses `FakeLLMProvider` (offline,
  deterministic). No real OpenAI/Anthropic provider exists or is enabled; the
  loader fails closed. No env-var key is read; no real API call is made.
- **Fake planner is deterministic.** `FakePlanner` maps a marker to a fixed plan
  (`FAKE_PLAN_INSPECT_PROJECT` / `FAKE_PLAN_FULL_BROWSER_E2E` /
  `FAKE_PLAN_PATCH_ONLY`, else a noop). Same input → same plan.
- **Planner is plan-only.** The `planner` eval category produces and validates a
  plan and **never executes** a step.
- **Execution bridge only accepts a validated plan.** `build_execution_sequence`
  re-checks `PlanValidationResult.valid`; an unvalidated/invalid plan fails closed
  (no execution).
- **Allowlisted skills only.** `inspect_project`, `start_local_server`,
  `open_localhost_browser`, `read_browser_console`, `patch_file_and_run_tests`.
  Any other skill is rejected.
- **No direct shell.** Denylisted names (`raw_shell`, `direct_command`, `eval`,
  `exec`, `bash`, `python_exec`, `arbitrary_tool`) are rejected. Shell only ever
  runs *inside* a vetted, registered skill — never as a planner/bridge command.
- **No autonomous replan.** The bridge maps a plan to a sequence once and runs it.
  No retry, no re-plan, no repair loop.
- **High-risk requires approval.** A `risk_level=high` step runs only with
  `requires_approval=true` **and** `--approve-high-risk`; otherwise fail closed.

## Results (frozen)

| Eval | Category | Score | Where |
|---|---|---|---|
| `fake_full_browser_plan` | planner (plan-only) | **1.0** | system interpreter |
| `fake_patch_plan_execution` | planner_execution | **1.0** | system interpreter |
| `fake_full_browser_plan_execution` | planner_execution | **1.0** | real browser via `scripts/run_full_browser_gate.py` (.venv) |
| `full_browser_vite_login_bug_e2e` | browser | **1.0** (still) | real browser via the gate (.venv) |

- **secret hygiene: PASS.** All plan/execution artifacts (`plan.json`,
  `plan_execution_trace.jsonl`, `plan_execution_summary.md`, `score.json`,
  `task.yaml`) are redacted; the free-form goal is redacted at the door.
- **unit tests: 234/234.**

## Chain

```
FakeLLMProvider (offline, deterministic)
  → FakePlanner            (marker → declarative Plan)
  → validate_plan          (unique ids, deps, risk, no direct shell, no secret)
  → ExecutionBridge        (allowlist + approval; plan → aliased skill sequence)
  → Orchestrator           (category: planner_execution; Safety Gate on each cmd)
  → SkillExecutor          (start_local_server → open/console pre → patch →
                            re-open/console post)
  → Evaluator              (inner real-skill score + bridge criteria)
```

## Active overrides (unchanged)

```text
open_localhost_browser     -> open_localhost_browser_v1
patch_file_and_run_tests   -> patch_file_and_run_tests_v2
read_browser_console       -> read_browser_console_v1
start_local_server         -> start_local_server_v1   (release 1.2)
```

## Frozen constraints

- **stable skills / safety_gate / promotion_policy untouched** throughout.
- All real implementations live as candidates under `harnesses/candidates/`.
- No `.venv` / browser cache / runs / screenshots / secrets are committed.

## Next possible phase (none started — decision point)

a. **Auto Repair Loop** — failure_report → repair proposal → candidate → eval.
   **Blocked behind a new gate:** must NOT modify stable directly; must be
   *repair-proposal only*; must run in a candidate workspace; must have an
   approval gate. **Auto-repair is not started.**
b. **Human review / staging / stable promotion** of the shell-executing candidates.
c. **UI dashboard** (the `apps/` surface).
d. **Real provider implementation** (operator opt-in; still fail-closed by default).
