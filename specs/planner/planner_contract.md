# Planner Contract (fake-only — plan, never execute)

The planner turns a user goal / marker into a **declarative, validated plan**. It
is the layer between "what the user wants" and "what skills the harness could
run". This phase ships a **fake-only** planner; there is no real LLM reasoning and
no execution.

See `src/planner/`, `scripts/plan_task.py`, `specs/llm/llm_provider_contract.md`,
and `docs/secrets_policy.md`.

## Hard guarantees

- **Plan only — the planner NEVER executes a step.** It emits `PlanStep`s
  (skill + inputs + expected outputs + success criteria + risk + depends_on); it
  never runs a shell command, browser action, server, or patch. Execution is a
  separate, gated layer.
- **Fake provider only.** The planner uses `FakeLLMProvider` (offline,
  deterministic). It performs **no network call, no env-var read, no real API
  call**. A provider with `real_api_enabled=True` is refused.
- **Redaction always.** Every provider response is passed through
  `src/llm/redaction.py` before it is kept, so no secret-looking text can reach a
  trace / report / plan file. Rendered plans (`plan.json`, markdown) are redacted.
- **No direct shell.** The validator rejects any step whose skill is a raw-shell /
  eval / exec name (`raw_shell`, `direct_command`, `shell`, `bash`, `sh`, `eval`,
  `exec`, `system`, `subprocess`, …), and any inputs that smuggle a raw command
  (`shell`, `raw_command`, `cmd`, …). Shell only ever happens *inside* a vetted,
  registered skill, never as a planner-chosen command.

## Markers (deterministic plans)

`FakePlanner` selects a plan from an explicit `marker` (or detects it as a
substring of the goal):

| Marker | Plan |
| --- | --- |
| `FAKE_PLAN_INSPECT_PROJECT` | `inspect_project` only |
| `FAKE_PLAN_FULL_BROWSER_E2E` | `start_local_server` → open + console (pre) → `patch_file_and_run_tests` → **re-open + console (post)** |
| `FAKE_PLAN_PATCH_ONLY` | `inspect_project` → `patch_file_and_run_tests` |
| (no marker) | a single harmless `noop` step |

Same input → same plan (deterministic).

## Plan validation rules (`plan_validator.validate_plan`)

A plan is valid only when ALL hold:

1. Every `step.id` is non-empty and unique.
2. Every `step.skill` is non-empty and not a forbidden direct-shell skill.
3. Every `depends_on` entry references an existing step id (and no self-dependency).
4. `risk_level` ∈ {`low`, `medium`, `high`}.
5. A `high` risk step must set `requires_approval=true`.
6. No step inputs use a forbidden raw-command key.
7. No step inputs contain a secret-looking value (redaction would change them).

## Planner-category evals

An eval with `category: planner` runs **only** the planner: the orchestrator
builds the plan, validates it, scores its *shape*, and writes `plan.json`,
`score.json`, `summary.md`. **No skill, server, browser, or patch is executed**
(`score.json` records `executed: false`). Existing browser/patch evals are
unaffected. See `evals/planner/fake_full_browser_plan.yaml`.

## Out of scope (explicitly)

- No real OpenAI/Anthropic call, no key read — fake provider only.
- No plan execution, no auto-repair loop — those are separate, gated phases.
- No UI, no multimodal, no new data channels.
