# Quick Resume (read me first when coming back)

One-minute orientation. For detail see
[`candidate_status_matrix.md`](candidate_status_matrix.md),
[`promotion_readiness_review.md`](promotion_readiness_review.md), and
[`next_milestone_plan.md`](next_milestone_plan.md).

**Latest checkpoint:**
[`checkpoints/checkpoint-phase-4-approved-patch-application.md`](checkpoints/checkpoint-phase-4-approved-patch-application.md)
— Approved Patch Application v0, **workspace-only** (human-approved proposal →
workspace-only apply → proposed_changes → fixed test allowlist → apply report);
**no stable change, no merge, no promotion**. (Earlier:
[`checkpoint-phase-3-repair-proposal-only.md`](checkpoints/checkpoint-phase-3-repair-proposal-only.md)
— Auto Repair Loop v0 proposal-only;
[`checkpoint-phase-2a-fake-planner-execution.md`](checkpoints/checkpoint-phase-2a-fake-planner-execution.md)
— fake planner execution bridge green;
[`checkpoint-phase-1b-full-browser-e2e.md`](checkpoints/checkpoint-phase-1b-full-browser-e2e.md)
— full real-browser e2e green;
[`checkpoint-0-to-1-harness-gates.md`](checkpoints/checkpoint-0-to-1-harness-gates.md).)

**Phase report:**
[`../reports/phase_4_approved_patch_application/README.md`](../reports/phase_4_approved_patch_application/README.md)
— Phase 4 Approved Patch Application v0, workspace-only (pipeline, results, risks).
Earlier:
[`../reports/phase_3_repair_proposal_only/README.md`](../reports/phase_3_repair_proposal_only/README.md),
[`../reports/phase_0_to_1_harness_mvp/README.md`](../reports/phase_0_to_1_harness_mvp/README.md).

Branch B draft (apply only after the Playwright gate passes — not current status) exists at [`branch_b_playwright_gate_passed_draft/`](branch_b_playwright_gate_passed_draft/README.md).

**Progress log:** [`progress_log.md`](progress_log.md) — chronological status + verified health.

## Current active overrides

The harness overlay resolver currently activates these candidates (highest
active version per overridden skill):

```text
open_localhost_browser     -> open_localhost_browser_v1
patch_file_and_run_tests   -> patch_file_and_run_tests_v2
start_local_server         -> start_local_server_v1   (release 1.2)
```

`read_browser_console` has **no candidate** — it runs the stable placeholder and
is intentionally **blocked** from getting one yet.

## Planner status: fake-only / no execution

`src/planner/` (`FakePlanner`) is **fake-only and plan-only** — it builds a
deterministic, validated plan from a marker and **never executes a step** (no real
API call, no env read, no auto-repair). Markers: `FAKE_PLAN_INSPECT_PROJECT`,
`FAKE_PLAN_FULL_BROWSER_E2E`, `FAKE_PLAN_PATCH_ONLY`, else noop. Try:
`python scripts/plan_task.py --goal "FAKE_PLAN_FULL_BROWSER_E2E" --marker FAKE_PLAN_FULL_BROWSER_E2E --json`.
Planner eval `evals/planner/fake_full_browser_plan.yaml` → **1.0**. Contract:
[`../specs/planner/planner_contract.md`](../specs/planner/planner_contract.md).

## Planner execution bridge status: allowlisted / no autonomy

`src/planner/execution_bridge.py` runs a **validated** fake plan as an
**allowlisted** skill sequence (no direct shell, no unapproved high-risk step, **no
autonomous replan**; execution context from a fixed per-marker registry). Distinct
from the plan-only `planner` category — `planner_execution` actually executes.
`evals/planner/fake_patch_plan_execution.yaml` → **1.0** (system py);
`evals/planner/fake_full_browser_plan_execution.yaml` → **1.0** via
`python scripts/run_full_browser_gate.py` (real browser, same chain as the e2e).
Dry-run anywhere: `python scripts/execute_plan.py --marker FAKE_PLAN_FULL_BROWSER_E2E --dry-run`.
Contract: [`../specs/planner/plan_execution_bridge_contract.md`](../specs/planner/plan_execution_bridge_contract.md).

## Repair status: proposal (v0) + approved apply (v0, workspace-only)

Auto Repair Loop **v0 — PROPOSAL ONLY.** `src/repair/` reads a failed eval
(`FailureAnalyzer`), generates a deterministic fake `RepairProposal`
(`FakeRepairPlanner`, fake provider), validates it, and writes a redacted proposal
workspace. `repair_propose.py --apply` is rejected.
`evals/repair/fake_repair_proposal_only.yaml` → **1.0**.

**Approved Patch Application v0 — WORKSPACE ONLY.** `scripts/repair_apply.py` now
exists: it takes a **human-approved** proposal (`APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY`
marker + named reviewer) and **only with `--approved`** materializes the approved
changes into an **apply workspace** (`apply_manifest.json` + `proposed_changes/` +
`apply_report.md` + `test_results.json`). **No stable merge, no real target file
written, no promotion**; without `--approved` it is rejected; it runs only a
**fixed test command allowlist** (never proposal-derived).
`evals/repair/fake_approved_patch_application.yaml` → **1.0**.
Try: `python scripts/repair_apply.py --proposal-workspace fixtures/repair/fake_approved_proposal_workspace --dry-run`.
Contracts: [`../specs/repair/repair_loop_contract.md`](../specs/repair/repair_loop_contract.md),
[`../specs/repair/approved_patch_application_contract.md`](../specs/repair/approved_patch_application_contract.md).

## What is green now

- `python scripts/run_demo.py --demo vite_login_bug` → **1.0**
  (real server keep_alive + http_fallback browser load + real patch).
- `python scripts/run_eval.py --task evals/browser/open_localhost_keep_alive_smoke.yaml` → **1.0**
  (but `browser_engine=http_fallback`, `browser_is_real=false`).
- `python scripts/run_eval.py --task evals/patch_runner/py_calc_bug_e2e.yaml` → **1.0**.
- **Real browser (via `.venv`):** `python scripts/run_full_browser_gate.py` →
  **`full_browser_vite_login_bug_e2e` 1.0** (engine=playwright, is_real_browser=true;
  pre-patch console error collected, post-patch fatal=0). Also
  `read_browser_console_smoke` 1.0 and `open_localhost_playwright_required_smoke` 1.0.
- **Planner execution bridge:**
  `python scripts/run_eval.py --task evals/planner/fake_patch_plan_execution.yaml` →
  **`fake_patch_plan_execution` 1.0** (system interpreter), and
  **`fake_full_browser_plan_execution` 1.0** via the real-browser gate (.venv) —
  same chain as the e2e, driven by a validated fake plan through the bridge.
- Plan-only planner: `fake_full_browser_plan` → **1.0**.
- **Repair proposal (v0, proposal-only):**
  `python scripts/run_eval.py --task evals/repair/fake_repair_proposal_only.yaml` →
  **`fake_repair_proposal_only` 1.0**; `repair_propose.py` is **proposal-only**
  and its **`--apply` is rejected** (exit 3).
- **Approved patch application (v0, workspace-only):**
  `python scripts/run_eval.py --task evals/repair/fake_approved_patch_application.yaml` →
  **`fake_approved_patch_application` 1.0**; `repair_apply.py` is **workspace-only**,
  needs `--approved` (else rejected), **stable untouched**, **no auto promotion**.
- `python scripts/run_unit_tests.py` → all pass. `validate_structure` /
  `validate_workflows` / `run_skill_tests` pass.
- No lingering server/browser processes after runs; the `_sessions` registry is
  empty after a clean run.

## What is blocked

- **read_browser_console_v1 exists — `dev`.** Real Playwright console collector;
  **no http_fallback** (`http_fallback_not_allowed`), forces
  `browser_mode=playwright`. `read_browser_console_smoke` = 1.0 in a Playwright env.
  A console on the http_fallback would be fake (ADR-013).
- **open_localhost_browser_v1 is `staging-ready`.** The Playwright real-browser
  gate PASSED (`engine=playwright`, `is_real_browser=true`) — Branch B applied.
  The http_fallback path is still a smoke only (**http_fallback is not a real
  browser**); promote to `staging` on operator approval.
- **full_browser_vite_login_bug_e2e is an executable gate — PASSING 1.0** via
  `python scripts/run_full_browser_gate.py` in a Playwright env (start → real
  browser → console pre → patch+tests → re-open → console post → fatal=0).
- `patch_file_and_run_tests_v2` is staging-ready but needs a human shell-execution
  review before `stable`.

**Next step: decision point (none started) — pick one:**

- **A. Merge + Promotion of an apply workspace** — a human merges an apply
  workspace's proposed change into a **candidate** (never stable directly), runs
  the regression gates, then the promotion policy applies. **Merge not started /
  promotion not started; no merge tooling.** Blocked behind a human approval gate
  (candidate workspace only, targeted tests + regression, rollback plan, promotion
  policy; never modify stable directly).
- **B. Human review / staging / stable promotion** of the shell-executing candidates.
- **C. UI dashboard** (the `apps/` surface).
- **D. Real provider implementation** (operator opt-in; fail-closed by default).

See `next_milestone_plan.md` for prerequisites + gates not to skip.
**Real-browser evals + gates run via the project `.venv`** (Playwright installed there).
**http_fallback is not a real browser.** stable / safety_gate / promotion_policy untouched.

## Dry-run gate commands (safe anywhere — no browser, no install)

```bash
python scripts/run_playwright_gate.py --dry-run
python scripts/run_full_browser_gate.py --dry-run
```

## What NOT to do yet

- Do not commit `.venv`, the ms-playwright browser cache, `runs/`, screenshots, or
  any secret.
- Run `python scripts/run_full_browser_gate.py` / `run_playwright_gate.py`
  (non-dry-run) only with Playwright + Chromium (the project `.venv`). `--dry-run`
  is safe anywhere.
- Do not promote any shell-executing candidate to `stable` without a human
  shell-execution + policy review.
- Do not start the next product phase (planner / auto-repair / UI / multimodal)
  without going through the candidate + promotion workflow and its gate.
- Do not add a scheduled reaper / cron / loop.
- Do not modify stable skills, `safety_gate`, or `promotion_policy`.

## Exact next real step

Phases 1A + 1B are **done** (Playwright gate, console smoke, and the full
real-browser e2e are all green). The next step is a **product decision** — pick
one and take it through the candidate + promotion workflow:

- **A. LLM planner**, **B. auto-repair loop**, **C. UI dashboard**, or
  **D. multimodal / data channels**.

See `next_milestone_plan.md` for each route's prerequisites and the gates not to
skip. To re-verify the current state, run the real-browser gates via the `.venv`:
`python scripts/run_full_browser_gate.py` (must stay 1.0).
