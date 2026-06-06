# Demo script — Fake Planner Execution

A short, reproducible walk-through of the Phase 2A chain: **fake provider →
validated plan → allowlisted execution bridge → full real-browser chain**.

## Demo goal

Show that a *fake, deterministic* planner can produce a plan that, after
validation, is executed by the orchestrator through an allowlisted bridge — with
**no real LLM, no direct shell, and no autonomous replan** — and that the
full-browser plan runs the same real-browser chain as the Phase 1B e2e.

## Commands

```bash
# 1) Plan only — build + validate a plan, print a redacted JSON summary.
python scripts/plan_task.py --goal "FAKE_PLAN_FULL_BROWSER_E2E" \
    --marker FAKE_PLAN_FULL_BROWSER_E2E --json

# 2) Bridge dry-run — show the allowlisted executable sequence, run NOTHING.
python scripts/execute_plan.py --goal "FAKE_PLAN_FULL_BROWSER_E2E" \
    --marker FAKE_PLAN_FULL_BROWSER_E2E --dry-run

# 3) Execute through the bridge over the real-browser chain (needs Playwright;
#    run via the project .venv / the full-browser gate).
python scripts/run_eval.py --task evals/planner/fake_full_browser_plan_execution.yaml
```

## Expected output

1. **`plan_task ... --json`** → a redacted JSON document with `validation.valid =
   true` and 6 steps: `start_local_server → open_pre → console_pre → patch →
   open_post → console_post`.
2. **`execute_plan ... --dry-run`** → prints `bridge_ok: True` and the executable
   sequence (each `plan_step → skill (as alias, risk=…)`), then
   `[DRY-RUN] no skill executed, nothing written.` (exit 0). **Nothing runs.**
3. **`run_eval ... fake_full_browser_plan_execution`** → in a Playwright env,
   `[PASS] fake_full_browser_plan_execution score=1.0` with all bridge criteria
   met (`allowed_skills_only`, `*_invoked`, `post_patch_reverify_invoked`,
   `score_1_0`, `no_lingering_process`, `no_secret_in_artifacts`). Under the
   system interpreter (no Playwright) it degrades — `score_1_0` is not met — which
   is expected; use the `.venv` / `scripts/run_full_browser_gate.py`.

## How to explain it

- **Fake provider.** The planner depends on `FakeLLMProvider` — offline,
  deterministic, **no network and no env-var key read**. There is no real
  OpenAI/Anthropic call; the real provider is intentionally not implemented and
  the loader fails closed. So the demo is fully reproducible and safe in CI.
- **No direct shell.** The plan validator and the bridge both reject any
  shell/eval/exec-style skill name. A shell command can only run *inside* a vetted,
  registered skill (e.g. `start_local_server`), never as something the planner or
  bridge chose. The planner never emits a command string.
- **Allowlisted skills.** The bridge executes only five skills
  (`inspect_project`, `start_local_server`, `open_localhost_browser`,
  `read_browser_console`, `patch_file_and_run_tests`). Anything else is rejected
  before execution.
- **No autonomous replan.** The bridge maps the plan to a sequence **once** and
  runs it. There is no retry, no re-plan, and no repair loop — auto-repair is a
  separate, not-yet-started phase.
- **Full browser execution from a validated plan.** The full-browser plan, after
  validation, drives the exact Phase 1B chain (start → open/console pre → patch →
  re-open/console post) on a **real** Playwright browser and reaches 1.0 — proving
  the bridge runs real work, not a mock, while staying inside the allowlist.

## Safety notes

- Default is dry-run; `--execute` is required to run anything.
- Only known markers have a vetted execution context (fixture / patch_plan /
  start_command); an unknown marker cannot be executed.
- All artifacts are redacted; no secret is ever written to `runs/`.
- This demo touches no stable skill, `safety_gate`, or `promotion_policy`.
