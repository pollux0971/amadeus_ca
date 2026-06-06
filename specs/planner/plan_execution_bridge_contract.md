# Plan Execution Bridge Contract (allowlisted, plan-validated, no autonomy)

The execution bridge turns a **validated** fake-planner `Plan` into a controlled,
allowlisted skill sequence the existing orchestrator can run. It is the gate
between "a plan exists" and "skills actually run". It is deliberately **not** a
general autonomous agent.

See `src/planner/execution_bridge.py`, `scripts/execute_plan.py`,
`specs/planner/planner_contract.md`, and `docs/secrets_policy.md`.

## Hard guarantees

- **Only a validated plan executes.** The bridge re-checks
  `PlanValidationResult.valid` (validating itself if the caller did not). An
  unvalidated / invalid plan → `ok=False`, **no execution** (fail closed).
- **Allowlisted skills only.** v1 allowlist:
  `inspect_project`, `start_local_server`, `open_localhost_browser`,
  `read_browser_console`, `patch_file_and_run_tests`. Any other skill → rejected.
- **No direct shell.** Direct shell is forbidden: denylisted skill names
  (`raw_shell`, `direct_command`, `eval`, `exec`, `bash`, `python_exec`,
  `arbitrary_tool`) are rejected outright. Shell only ever runs *inside* a vetted,
  registered skill — never as a planner- or bridge-chosen command.
- **Approval policy.**
  - `risk_level=low` → executes.
  - `risk_level=medium` → executes, but the risk is recorded (`risk_notes`).
  - `risk_level=high` → executes **only** when the step sets
    `requires_approval=true` **and** the caller passes `--approve-high-risk`
    (`approve_high_risk=true`). Otherwise → fail closed.
- **No autonomous replan.** The bridge maps a plan to a sequence once and runs it.
  It never regenerates, retries, or repairs the plan — there is no loop.
- **No LLM call, no plan mutation, no Safety Gate bypass.** The bridge calls no
  provider, never mutates the input plan, and the orchestrator still runs the
  Safety Gate command check on every command the skills emit.
- **No secret in trace.** Plan execution artifacts (`plan.json`,
  `plan_execution_trace.jsonl`, `plan_execution_summary.md`, `score.json`,
  `task.yaml`) are redacted via `src/llm/redaction.py`. No secret-looking value is
  ever written.

## Step → sequence mapping

Each `PlanStep` becomes one eval-runner entry `{skill, as}`. A skill that appears
once keeps its name as the alias; a skill that repeats uses the plan step id
(`open_pre` / `open_post` / `console_pre` / `console_post`) so the orchestrator's
phase-aware evidence rules line up with the existing real-browser chain.

## Execution context (the planner never supplies shell)

The *plan* is declarative. The concrete fixture / `patch_plan` / `start_command`
needed to run the allowlisted skills come from a fixed, vetted **per-marker
registry** in the bridge (`execution_context_for`), keyed by the fake planner's
deterministic marker — NOT from planner output. An unknown marker has no context
and cannot be executed. This is what keeps planner text from ever becoming a
shell command.

## `planner_execution` eval category

An eval with `category: planner_execution` builds the fake plan, validates it,
bridges it, and **executes the allowlisted sequence** under the Safety Gate
(`score.json` records `executed: true`, `bridge_ok`, `inner_score`). This is
distinct from the plan-only `planner` category, which still **only plans and never
executes**. The two categories do not replace each other.

- `score_1_0` is met only when the underlying real skill chain scores 1.0 (e.g.
  the full real-browser e2e — which needs a real Playwright browser, run via
  `scripts/run_full_browser_gate.py`).
- `no_lingering_process` requires every browser/console step to have closed its
  resources and the kept-alive server to be torn down at end of run.

## Out of scope (explicitly)

- No real OpenAI/Anthropic call, no key read — fake provider only.
- No auto-repair / replan loop, no general autonomous agent.
- No UI, no multimodal, no new data channels.
