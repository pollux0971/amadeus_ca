# Quick Resume (read me first when coming back)

One-minute orientation. For detail see
[`candidate_status_matrix.md`](candidate_status_matrix.md),
[`promotion_readiness_review.md`](promotion_readiness_review.md), and
[`next_milestone_plan.md`](next_milestone_plan.md).

**Demo package (single entry to present the project):**
[`../demo_package/README.md`](../demo_package/README.md) — overview, architecture,
safe demo commands, dashboard, phase timeline, safety boundaries, teacher outline.

## Test environment baseline (read before judging a test failure)

Two interpreters, by design — **don't mistake an environment gap for a regression.**
Authoritative ref: [`test_environment_baseline.md`](test_environment_baseline.md);
live summary via `.venv/bin/python scripts/check_test_environment_baseline.py`.

- **`python` is often not on `PATH`** → use an explicit interpreter; a missing bare
  `python` is a **warning, never a failure**.
- **Real-browser gates should use `.venv/bin/python`** (Playwright + Chromium live
  there): `.venv/bin/python scripts/run_full_browser_gate.py`,
  `.venv/bin/python scripts/run_dashboard_smoke.py`. `http_fallback` is **not** a real
  browser. Dry-runs / non-browser checks are safe on either interpreter.
- **Unit baseline:** system `/usr/bin/python3` → **519/519**; `.venv/bin/python` →
  **517/519**. The 2 `.venv` "failures" are **known environment-gap** tests that
  assume Playwright is *absent* (`test_browser_keep_alive_e2e.py::...` and
  `test_full_browser_gate_script.py::test_missing_prereqs_block_with_exit_2`) — they
  pass on system Python and are **not regressions**. A `.venv` failing set that is
  **anything other than exactly those two** is a regression to investigate — never use
  the baseline to hide a new failure.

**Real provider (v0, fake still default):** `src/llm/openai_provider.py` +
`anthropic_provider.py` now exist (stdlib `urllib`). **Fake stays default;
fail-closed**; key read only from the named env var at call time; all output
redacted; **no real API call by default** (operator opt-in via
`python scripts/llm_provider_smoke.py --provider openai --dry-run`, real call needs
`--real-call` + `allow_real_api_calls=true` + env var). Contract:
[`../specs/llm/llm_provider_contract.md`](../specs/llm/llm_provider_contract.md).

**OpenAI Real Provider Live Smoke v0 (OpenAI only; dry-run default; fail-closed):**
`scripts/real_provider_live_smoke.py` proves the OpenAI provider can complete **one
minimal real call**. **Dry-run by default** (config / env-var NAME / construction /
redaction; **no network**); a real call needs **`--real-call` + `OPENAI_API_KEY`
present**, else **exit 2 = BLOCKED**. The prompt is **FIXED**
(`Reply with exactly: provider-ok`), `max_tokens` is a small safe default, and every
output + the `live_smoke_report.json/.md` (under the gitignored
`runs/real_provider_live_smoke/`) is **redacted** — the key is read only from the env
var at call time and never printed/committed. **Anthropic is BLOCKED / NOT TESTED**
this round. **No planner / plan execution / auto-repair / stable promotion.** Wired
into `validate_workflows.py` (dry-run only). See
[`real_provider/README.md`](real_provider/README.md).
```bash
python scripts/real_provider_live_smoke.py --provider openai --dry-run             # safe anywhere
python scripts/real_provider_live_smoke.py --provider openai --real-call --expect provider-ok  # operator opt-in
```

**Project report (formal write-up draft):**
[`../project_report/README.md`](../project_report/README.md) — 12 sections (abstract →
presentation script), for course report / instructor review / slides.

**Stable promotion readiness audit:**
[`../reports/stable_promotion_readiness_audit_v0/README.md`](../reports/stable_promotion_readiness_audit_v0/README.md)
— **recommendation NO-GO / BLOCKED** (engineering gates green; human gates unmet);
stable promotion not started.

**Backlog (what to do next):** the Epic / Story backlog is at
[`../docs/epics/README.md`](epics/README.md); choose **one bounded story** via
[`../docs/epics/decision_matrix.md`](epics/decision_matrix.md). A `/goal` run
executes exactly one bounded story (no auto-extend); see `docs/epics/`.
**Planning-only stories completed:** UI dashboard
([`../docs/ui_dashboard/`](ui_dashboard/)), real provider
([`../docs/real_provider/`](real_provider/)), and **multimodal / data channel
planning completed** ([`../docs/multimodal_data_channels/`](multimodal_data_channels/)).
**UI dashboard skeleton (read-only) completed** — `ui_dashboard/` static skeleton +
`scripts/generate_dashboard_snapshot.py` + `scripts/validate_dashboard.py`;
**read-only, no action execution, no secret display**
([`../reports/story_ui_dashboard_skeleton_v0/README.md`](../reports/story_ui_dashboard_skeleton_v0/README.md)).
**UI dashboard real-browser smoke gate completed** —
`python scripts/run_dashboard_smoke.py` → `ui_dashboard_readonly_smoke` **1.0** in a
real Playwright browser (read-only verified, no external request, no lingering
process; `--dry-run` safe anywhere)
([`../reports/story_ui_dashboard_smoke_v0/README.md`](../reports/story_ui_dashboard_smoke_v0/README.md)).
Remaining: **Stable Promotion remains blocked** behind human/policy/rollback/shell-review gates.

**Latest checkpoint:**
[`checkpoints/checkpoint-phase-6-staging-promotion.md`](checkpoints/checkpoint-phase-6-staging-promotion.md)
— Staging Promotion v0, **staging-workspace-only** (human-reviewed candidate merge
workspace → staging promotion workspace → rollback verification → stable promotion
checklist); **no active candidate change, no stable change, stable promotion not
started**. (Earlier:
[`checkpoint-phase-5-candidate-merge.md`](checkpoints/checkpoint-phase-5-candidate-merge.md)
— candidate merge v0 candidate-workspace-only;
[`checkpoint-phase-4-approved-patch-application.md`](checkpoints/checkpoint-phase-4-approved-patch-application.md)
— approved patch application v0 workspace-only;
[`checkpoint-phase-3-repair-proposal-only.md`](checkpoints/checkpoint-phase-3-repair-proposal-only.md)
— Auto Repair Loop v0 proposal-only;
[`checkpoint-phase-2a-fake-planner-execution.md`](checkpoints/checkpoint-phase-2a-fake-planner-execution.md)
— fake planner execution bridge green;
[`checkpoint-phase-1b-full-browser-e2e.md`](checkpoints/checkpoint-phase-1b-full-browser-e2e.md)
— full real-browser e2e green;
[`checkpoint-0-to-1-harness-gates.md`](checkpoints/checkpoint-0-to-1-harness-gates.md).)

**Phase report:**
[`../reports/phase_6_staging_promotion/README.md`](../reports/phase_6_staging_promotion/README.md)
— Phase 6 Staging Promotion v0, staging-workspace-only (pipeline, results, risks).
Earlier:
[`../reports/phase_5_candidate_merge/README.md`](../reports/phase_5_candidate_merge/README.md),
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

## Planner status: fake-only default / no execution

`src/planner/` (`FakePlanner`) is **fake-only and plan-only** — it builds a
deterministic, validated plan from a marker and **never executes a step** (no real
API call, no env read, no auto-repair). Markers: `FAKE_PLAN_INSPECT_PROJECT`,
`FAKE_PLAN_FULL_BROWSER_E2E`, `FAKE_PLAN_PATCH_ONLY`, else noop. Try:
`python scripts/plan_task.py --goal "FAKE_PLAN_FULL_BROWSER_E2E" --marker FAKE_PLAN_FULL_BROWSER_E2E --json`.
Planner eval `evals/planner/fake_full_browser_plan.yaml` → **1.0**. Contract:
[`../specs/planner/planner_contract.md`](../specs/planner/planner_contract.md).

**Provider-aware planner (v0, fake-only default, plan-only).**
`src/planner/provider_planner.py` (`ProviderBackedPlanner` +
`build_planner_from_config`) wires the real provider runtime into the planner behind
the **fail-closed** loader. The **fake provider is still the default**; a real
provider is constructed only under config opt-in (`provider != fake` +
`allow_real_api_calls=true` + `api_key_env`), else it fails closed. In a dry-run the
real provider is **HELD but never called** — the plan is still built deterministically
from the marker, and the planner **never executes a step** (no real API call). Try:
`python scripts/plan_task.py --marker FAKE_PLAN_INSPECT_PROJECT --from-config` and
`python scripts/planner_provider_smoke.py --provider openai --dry-run` (dry-run only,
no real-call path). Eval `evals/planner/provider_backed_plan_dry_run.yaml` → **1.0**.

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

## Repair status: proposal + apply + merge + staging (all v0, workspace-only)

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

**Candidate Merge v0 — CANDIDATE WORKSPACE ONLY.** `scripts/repair_merge.py` now
exists: it takes a **human-approved** apply workspace
(`APPROVED_FOR_CANDIDATE_MERGE` marker + named reviewer) and **only with
`--approved` + a non-empty `--reviewer`** merges the proposed changes into a **new
candidate merge workspace** (`merge_manifest.json` + `merged_changes/` +
`merge_report.md` + **`rollback_plan.md`** + **`promotion_review_package.md`** +
`test_results.json`). **No stable promotion, no active-candidate change, no real
target file written, no promotion**; without `--approved`/reviewer it is rejected;
fixed test allowlist only. `evals/repair/fake_candidate_merge.yaml` → **1.0**.
Try: `python scripts/repair_merge.py --apply-workspace fixtures/repair/fake_approved_apply_workspace --dry-run`.

**Staging Promotion v0 — STAGING WORKSPACE ONLY.** `scripts/staging_promote.py` now
exists: it takes a **human-approved** candidate merge workspace
(`APPROVED_FOR_STAGING_PROMOTION` marker + named reviewer) and **only with
`--approved` + a non-empty `--reviewer`** promotes the merged changes into a **new
staging workspace** (`staging_manifest.json` + `staged_changes/` + `staging_report.md`
+ **`rollback_verification.md`** + `regression_results.json` +
**`stable_promotion_checklist.md`**). **No stable promotion, no active-candidate
change, no real target file written**; without `--approved`/reviewer it is rejected;
fixed test allowlist only; rollback verification generated; regression recorded.
`evals/repair/fake_staging_promotion.yaml` → **1.0**.
Try: `python scripts/staging_promote.py --merge-workspace fixtures/repair/fake_approved_merge_workspace --dry-run`.
Contracts: [`../specs/repair/repair_loop_contract.md`](../specs/repair/repair_loop_contract.md),
[`../specs/repair/approved_patch_application_contract.md`](../specs/repair/approved_patch_application_contract.md),
[`../specs/repair/candidate_merge_contract.md`](../specs/repair/candidate_merge_contract.md),
[`../specs/repair/staging_promotion_contract.md`](../specs/repair/staging_promotion_contract.md).

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
- **Candidate merge (v0, candidate-workspace-only):**
  `python scripts/run_eval.py --task evals/repair/fake_candidate_merge.yaml` →
  **`fake_candidate_merge` 1.0**; `repair_merge.py` needs `--approved` + non-empty
  `--reviewer` (else rejected), writes a **candidate merge workspace only** with a
  **rollback plan generated** + **promotion review package generated**, **stable
  untouched**, **no auto promotion**.
- **Staging promotion (v0, staging-workspace-only):**
  `python scripts/run_eval.py --task evals/repair/fake_staging_promotion.yaml` →
  **`fake_staging_promotion` 1.0**; `staging_promote.py` needs `--approved` +
  non-empty `--reviewer` (else rejected), writes a **staging workspace only**.
  **rollback verification generated**, **regression recorded**, and **stable promotion checklist generated**; **stable untouched**; **no stable promotion**.
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

- **A. Stable Promotion** — a human reviews a staging workspace + its
  stable-promotion checklist, confirms the verified rollback + full regression,
  completes the human shell-execution review, then the promotion policy moves a
  candidate to `stable`. **Stable promotion not started.** Blocked behind a human
  approval gate (review the staging workspace, confirm verified rollback, full
  regression, human shell review, promotion policy; never modify stable directly).
- **B. UI dashboard** (the `apps/` surface).
- **C. Real provider implementation** (operator opt-in; fail-closed by default).

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
