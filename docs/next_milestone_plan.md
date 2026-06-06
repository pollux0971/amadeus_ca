# Next Milestone Plan

> **Quick resume pointer:** for a one-minute "where am I" summary (active
> overrides, what's green, what's blocked, dry-run commands, next real step), read
> [`docs/quick_resume.md`](quick_resume.md). The ordering below is unchanged.

Ordered plan after the candidate-status review. Each step has an explicit gate;
do not skip ahead. Nothing here installs Playwright/Chromium or modifies stable
skills, `safety_gate`, or `promotion_policy` — those are environment/operator
actions, not code changes in this repo.

## Fake LLM Planner v1 — status: ✅ DONE (fake-only, no execution)

`src/planner/` ships a **fake-only, plan-only** planner: `FakePlanner` (offline
`FakeLLMProvider`, deterministic), `plan_validator`, `plan_renderer`, plus
`scripts/plan_task.py`. The planner turns a goal/marker into a **declarative,
validated plan and never executes a step** — no real API call, no env-var read,
no auto-repair. Markers: `FAKE_PLAN_INSPECT_PROJECT`,
`FAKE_PLAN_FULL_BROWSER_E2E`, `FAKE_PLAN_PATCH_ONLY`, else a noop plan. Contract:
[`../specs/planner/planner_contract.md`](../specs/planner/planner_contract.md).

```bash
python scripts/plan_task.py --goal "FAKE_PLAN_FULL_BROWSER_E2E" \
    --marker FAKE_PLAN_FULL_BROWSER_E2E --json     # build+validate, prints redacted plan
python scripts/run_eval.py --task evals/planner/fake_full_browser_plan.yaml  # planner eval → 1.0
```

Planner eval `fake_full_browser_plan` scores **1.0**. Real LLM reasoning and the
auto-repair loop remain separate, **not-yet-started** phases.

## Fake Planner Execution Bridge v1 — status: ✅ DONE (allowlisted, no autonomy)

`src/planner/execution_bridge.py` turns a **validated** fake plan into an
**allowlisted** skill sequence the orchestrator runs under the Safety Gate. It is
**not** a general autonomous agent: only a validated plan executes, only
allowlisted skills (`inspect_project`, `start_local_server`,
`open_localhost_browser`, `read_browser_console`, `patch_file_and_run_tests`), no
direct shell, no unapproved high-risk step, **no autonomous replan**. Execution
context (fixture / patch_plan / start_command) comes from a fixed per-marker
registry — the planner never supplies a shell command. Contract:
[`../specs/planner/plan_execution_bridge_contract.md`](../specs/planner/plan_execution_bridge_contract.md).

```bash
python scripts/execute_plan.py --goal "FAKE_PLAN_FULL_BROWSER_E2E" \
    --marker FAKE_PLAN_FULL_BROWSER_E2E --dry-run    # safe anywhere; runs nothing
python scripts/run_eval.py --task evals/planner/fake_patch_plan_execution.yaml      # → 1.0 (system py)
# real-browser bridge eval (needs Playwright; run via the gate / .venv):
python scripts/run_full_browser_gate.py            # runs the e2e AND the bridge eval → 1.0
```

`fake_patch_plan_execution` → **1.0** under the system interpreter;
`fake_full_browser_plan_execution` → **1.0** via the real-browser gate (same
chain as `full_browser_vite_login_bug_e2e`). All execution artifacts are
redacted. The auto-repair loop remains **not-yet-started**.

**Phase 2A is complete and frozen** at
[`../docs/checkpoints/checkpoint-phase-2a-fake-planner-execution.md`](checkpoints/checkpoint-phase-2a-fake-planner-execution.md)
(tag `checkpoint-phase-2a-fake-planner-execution`).

**Phase 3 (Auto Repair Loop v0 — proposal-only) is complete and frozen** at
[`../docs/checkpoints/checkpoint-phase-3-repair-proposal-only.md`](checkpoints/checkpoint-phase-3-repair-proposal-only.md)
(tag `checkpoint-phase-3-repair-proposal-only`). `fake_repair_proposal_only` →
**1.0**; `repair_propose.py` is proposal-only; **`--apply` is rejected**; there is
**no `scripts/repair_apply.py`**. Contract:
[`../specs/repair/repair_loop_contract.md`](../specs/repair/repair_loop_contract.md);
report:
[`../reports/phase_3_repair_proposal_only/README.md`](../reports/phase_3_repair_proposal_only/README.md).

## Decision point — next phase (none started)

Pick one; each has a gate that must not be skipped:

- **A. Approved Patch Application** — a human approves a repair proposal and the
  change is applied. **Not started; no `scripts/repair_apply.py`.** Hard
  prerequisites before ANY apply code:
  - **Must NOT modify stable directly.**
  - **Must apply only to a candidate workspace** (isolated candidate dir).
  - **Must have human approval** (clear the proposal's `approval_checklist.md`).
  - **Must run targeted tests + regression** after applying.
  - **Must follow the promotion policy** (`specs/harness/promotion_policy.md`).
  - **Must keep a rollback** (the change is reversible).
- **B. Human review / staging / stable promotion** of the shell-executing
  candidates (`patch_file_and_run_tests_v2`, `start_local_server_v1.2`).
- **C. UI dashboard** — the `apps/` surface.
- **D. Real provider implementation** — operator opt-in only; fail-closed by
  default; never enabled automatically.

## Sequence

1. **Run the open_localhost_browser_v1 real-browser gate** in an environment that
   has Playwright + Chromium installed
   (`pip install playwright && playwright install chromium`). The gate is already
   scaffolded; run it with:

   ```bash
   python scripts/run_playwright_gate.py --dry-run   # safe anywhere: shows the checks/plan
   python scripts/run_playwright_gate.py             # only with Playwright + Chromium
   ```

   The runner checks the Playwright package and a Chromium runtime first (exit
   code 2 and a clear message if either is missing — it never installs anything),
   then runs `evals/browser/open_localhost_playwright_required_smoke.yaml`. That
   eval verifies the checks in
   `harnesses/candidates/open_localhost_browser_v1/playwright_verification_plan.md`:
   `engine=playwright`, `is_real_browser=true`, JS/console/screenshot supported, a
   screenshot artifact, and no lingering server.

   **Status: ✅ COMPLETED.** `python scripts/run_playwright_gate.py` PASSED — eval
   `open_localhost_playwright_required_smoke` scored **1.0** with
   `engine=playwright`, `is_real_browser=true`, screenshot + snapshot artifacts,
   and no lingering process. Evidence:
   `docs/checkpoints/phase_1a_playwright_gate_passed.md`.

2. ✅ **DONE — `open_localhost_browser_v1` is now `staging-ready`** (Branch B
   applied; `engine=playwright` / `is_real_browser=true` recorded). The
   http_fallback path is still a smoke only (**http_fallback is not a real
   browser**).

   ### ✅ IN PROGRESS: `read_browser_console_v1`
   Started. It **forces `browser_mode=playwright`** and fails with
   `browser_runtime_missing` when Playwright is absent — never a fabricated console
   (ADR-013). The **console smoke (`read_browser_console_smoke`) passes 1.0** in a
   Playwright environment (`engine=playwright`, `console_supported=true`).

   ### ✅ DONE: `read_browser_console` smoke completed
   `read_browser_console_smoke` passes 1.0 in a Playwright environment.

   ### ✅ DONE: full real-browser e2e wired + passing
   `full_browser_vite_login_bug_e2e` is now an **executable gate** and **passes
   1.0** via `python scripts/run_full_browser_gate.py` (start → real browser →
   console pre-patch → patch + tests → re-open → console post-patch → fatal=0). The
   evidence rules (`patch_applied` / `browser_reverify_passed` /
   `no_fatal_console_error_after_patch`) and the aliased pre/post-patch steps are
   wired. Evidence: `docs/checkpoints/phase_1b_full_browser_gate_passed.md`.

   ### ✅ Phase 1A + 1B COMPLETE
   Playwright real-browser gate passed; console smoke 1.0; full real-browser e2e
   1.0. The next milestone is **no longer the Playwright gate** — it is a product
   decision point.

## Decision point — choose the next phase (none started)

Each route goes through the candidate → eval → promotion workflow; do not skip
its gate.

- **A. LLM planner.** Replace rule-based step selection with a model planner.
  Prereq: a budget/eval harness for the planner; keep the deterministic harness as
  the fallback/oracle. Gate: planner must not regress any existing eval.
- **B. Claude / Codex auto-repair loop.** failure_report → propose candidate →
  eval → promotion. Prereq: stable trace/score/failure_report (already present);
  candidate isolation (worktree) for safety. Gate: every applied candidate must
  pass its eval + the regression suite; no auto-promotion past human shell review.
- **C. UI dashboard.** The `apps/` surface (trace/score viewer). Prereq: read-only
  over `runs/`; treat as a separate app surface (ADR-011). Gate: must not touch the
  harness runtime or weaken isolation.
- **D. Multimodal / data-channel extensions.** Via brownfield intake → manifest →
  adapter → eval → promotion. Prereq: `ArtifactRef` normalization (ADR-012). Gate:
  raw media never enters prompts directly.

### Gates not to skip (still)

- Stable promotion needs a human shell-execution review (patch runner,
  start_local_server) + the promotion policy review.
- **http_fallback is not a real browser**; real-browser work uses Playwright (via
  the project `.venv`).
- Do not modify stable skills, `safety_gate`, or `promotion_policy` outside the
  candidate + promotion workflow.

3. **Start `read_browser_console_v1`.** Only after step 2. It is **blocked** until
   a real browser exists, because a console on the http_fallback would be fake.

4. **`read_browser_console_v1` must force `browser_mode=playwright`.** It must
   require a real browser runtime and fail with `browser_runtime_missing` when
   Playwright is absent — never degrade to a fabricated console.

5. **Run `full_browser_vite_login_bug_e2e`** — the end-to-end chain on the real
   browser:
   - `start_local_server` (keep_alive)
   - → `open_localhost_browser` (real browser)
   - → `read_browser_console`
   - → `patch_file_and_run_tests`
   - → rerun + verify
   The orchestrator tears down the kept-alive server at the end of the run.

   The gate is already scaffolded (a **draft** eval + a runner); run it with:

   ```bash
   python scripts/run_full_browser_gate.py --dry-run   # safe anywhere: lists blocked prerequisites
   python scripts/run_full_browser_gate.py             # only when ALL prerequisites are met
   ```

   `run_full_browser_gate.py` refuses to run (exit code 2) until **all** of:
   (a) the Playwright package, (b) a Chromium runtime, (c) the
   `open_localhost_browser` real-browser gate has **passed**, and (d) a
   `read_browser_console` candidate **exists**. It installs nothing.

   **Status: the full-browser gate eval (`draft: true`,
   `blocked_until: playwright_gate_passed_and_console_skill_exists`) and its runner
   exist, but the gate is NOT yet runnable** — both the real-browser Playwright
   gate (step 1) and `read_browser_console_v1` (steps 3–4) must come first. This
   does **not** change the order: `read_browser_console` still cannot start early.

## Parallel, non-blocking items

- Human shell-execution review sign-off for `patch_file_and_run_tests_v2`
  (unblocks its move to `staging`) and for `start_local_server_v1.2`.
- Decide whether an OS-level guard (cgroup/systemd-scope or supervised reaper) is
  needed for `start_local_server` kept-alive servers — the current lease is
  advisory, not an OS-level watchdog.

## Explicitly out of scope right now

- Do not start `read_browser_console` (blocked).
- Do not add a scheduled reaper / cron / loop.
- Do not install Playwright/Chromium as part of this repo.
- Do not modify stable skills, `safety_gate`, or `promotion_policy`.
