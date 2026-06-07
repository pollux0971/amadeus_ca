# Next Milestone Plan

> **Quick resume pointer:** for a one-minute "where am I" summary (active
> overrides, what's green, what's blocked, dry-run commands, next real step), read
> [`docs/quick_resume.md`](quick_resume.md). The ordering below is unchanged.

Ordered plan after the candidate-status review. Each step has an explicit gate;
do not skip ahead. Nothing here installs Playwright/Chromium or modifies stable
skills, `safety_gate`, or `promotion_policy` — those are environment/operator
actions, not code changes in this repo.

## Real Provider Implementation v0 — DONE (fake still default, fail-closed)

Minimal real providers now exist: `src/llm/openai_provider.py` (chat completions) and
`src/llm/anthropic_provider.py` (messages), both stdlib `urllib`, plus
`scripts/llm_provider_smoke.py` (dry-run default). **The fake provider is still the
default and the loader is fail-closed**: a real provider is constructed only when
`provider != fake` AND `allow_real_api_calls=true` AND `api_key_env` is set. The key
is read only from the named env var at call time; every prompt/response/error is
redacted; **no real API call is made by default** (operator opt-in only, mocked in
tests). No planner integration, no auto-repair. Contract:
[`../specs/llm/llm_provider_contract.md`](../specs/llm/llm_provider_contract.md).

## Test Environment Baseline Normalization v0 — DONE (docs / checker / validator)

The system-Python vs `.venv`-Python test difference is now **documented and locked**
in [`test_environment_baseline.md`](test_environment_baseline.md), with a report-only
checker `scripts/check_test_environment_baseline.py` (no install, no network, no
secret) wired into `scripts/validate_workflows.py` as a **soft** check — a missing
bare `python` on PATH is a **warning, never a failure**, and a missing `.venv` /
Playwright is reported as WARNING/BLOCKED, not a hard gate fail. **Real-browser gates
must run on `.venv/bin/python`**; `http_fallback` is not a real browser. The two
`.venv` unit "failures" (`test_browser_keep_alive_e2e.py::...`,
`test_full_browser_gate_script.py::test_missing_prereqs_block_with_exit_2`) are
recorded as **known environment-gap** tests (they pass on system Python, 519/519) and
the doc gives the regression-vs-environment-gap rule — **never hide a new failure
behind the known baseline.** No runtime / stable / `safety_gate` / `promotion_policy`
change.

> **Execution-path rule for future stories.** Every story MUST state, per command,
> whether it runs on **system Python** or the **`.venv`** (`.venv/bin/python`). Any
> real-browser claim requires the `.venv` path; a result from an `http_fallback` run
> may not be reported as a real-browser result.

## OpenAI Real Provider Live Smoke v0 — DONE (OpenAI only; dry-run default; fail-closed)

`scripts/real_provider_live_smoke.py` (+ `tests/unit/test_real_provider_live_smoke_script.py`)
verifies that the **OpenAI** real provider can complete **one minimal real API call**,
while keeping every secrets-policy boundary. It is **dry-run by default** (config /
env-var NAME / provider construction / redaction; **no network**); a real call needs
explicit operator opt-in (`--real-call`) **and** `OPENAI_API_KEY` present at run time,
else it **fails closed (exit 2 = BLOCKED)**. The prompt is **FIXED**
(`Reply with exactly: provider-ok`, never arbitrary), `max_tokens` is a small safe
default (no long output), and stdout/stderr plus the `live_smoke_report.json` /
`live_smoke_report.md` artifacts (under the gitignored `runs/real_provider_live_smoke/`)
are **redacted** — the key is read only from the env var at call time and is never
printed, traced, committed, or stored in config (config holds the env-var NAME only).
**Anthropic is intentionally BLOCKED / NOT TESTED this round.** This story runs **no
planner, no plan execution, no auto-repair, and no stable promotion**, and touches no
stable skill / active candidate / `safety_gate` / `promotion_policy`. The live-smoke
safety check is wired into `scripts/validate_workflows.py` (dry-run only — the gate
makes no real API call). Contract / boundaries:
[`../specs/llm/llm_provider_contract.md`](../specs/llm/llm_provider_contract.md),
[`../docs/secrets_policy.md`](secrets_policy.md),
[`../docs/real_provider/README.md`](real_provider/README.md).

```bash
python scripts/real_provider_live_smoke.py --provider openai --dry-run             # safe anywhere; no API call
python scripts/real_provider_live_smoke.py --provider openai --real-call --expect provider-ok  # operator opt-in; needs OPENAI_API_KEY
```

## Dashboard Gate Status v0 — DONE (read-only status surfaces)

The read-only UI dashboard now surfaces the OpenAI / planner / read-only-execution
status. `scripts/generate_dashboard_snapshot.py` (redacted docs only — no API call, no
shell, no `.env`/`password`/`runs` read; refuses on any secret) adds six keys:
`openai_provider_status` (fake default, fail-closed, live smoke shipped, real call
operator-opt-in only — key referenced by env-var NAME only), `planner_live_status`
(plan-only; never executes; no auto-repair), `readonly_execution_status`
(human-approved; dry-run default; allowlisted read-only only), `readonly_allowlist`
(`inspect_project` + `list_project_files`, **display only**), `latest_gate_scores`
(the read-only eval gates' declared scores), and `blocked_items` (incl. **stable
promotion: BLOCKED**). The UI (`ui_dashboard/static/`) renders them via `textContent`
(no `innerHTML`/`eval`); **no button / form / onclick / POST / external fetch / secret
/ action trigger** — still status only. `scripts/validate_dashboard.py` enforces the
new keys, that the displayed allowlist is read-only only, and the new UI section ids;
the real-browser smoke (`evals/dashboard/ui_dashboard_readonly_smoke.yaml` +
`scripts/run_dashboard_smoke.py`) adds visibility criteria and stays **1.0**. Tests:
`tests/unit/test_dashboard_gate_status.py`; wired into `scripts/validate_workflows.py`.
No new action, no allowlist expansion, no real API call; stable skills / active
candidate / `safety_gate` / `promotion_policy` untouched.

```bash
python scripts/generate_dashboard_snapshot.py   # redacted docs only
python scripts/validate_dashboard.py
python scripts/run_dashboard_smoke.py           # real browser (.venv) → 1.0
```

## OpenAI Multi-Step Plan Review v0 — DONE (review-only; never executes)

`scripts/openai_multistep_plan_review.py` has the OpenAI live planner produce a
fixed-goal **two-step** read-only plan (`inspect_project` → `list_project_files`) and
emits a **human-review package** (`plan.json`, `plan_summary.md`, `risk_assessment.md`,
`approval_checklist.md` [**NOT APPROVED** by default], `execution_preconditions.md`,
`review_report.json` — all redacted). It is **plan-review only**: the plan is **never
executed**, **never auto-repaired**, never added to an approved fixture; no repair /
apply / merge / staging / promotion. **Dry-run by default** uses an offline
deterministic two-step plan (**no API call**); `--real-call` makes **one** OpenAI call
(provider=openai + `allow_real_api_calls=true` + the OpenAI key in `os.environ`, fixed
prompt only, fail-closed). The returned JSON plan must pass `PlanValidator`, be
multi-step, contain **only** `inspect_project` + `list_project_files`, and be all
low-risk, else a **BLOCKED** package is written (no auto-fix). Re-runnable eval
`evals/planner/openai_multistep_plan_review.yaml` (category `planner_multistep_review`)
→ **1.0** with no API call; the multistep **execution** eval stays **1.0**. The
read-only allowlist is **unchanged**. Report:
[`../reports/openai_multistep_plan_review_v0/README.md`](../reports/openai_multistep_plan_review_v0/README.md);
tests: `tests/unit/test_openai_multistep_plan_review.py`; wired into
`scripts/validate_workflows.py`. Stable skills / active candidate / `safety_gate` /
`promotion_policy` untouched.

```bash
python scripts/openai_multistep_plan_review.py --dry-run        # offline; no API
python scripts/openai_multistep_plan_review.py --real-call      # operator opt-in; one OpenAI call
python scripts/run_eval.py --task evals/planner/openai_multistep_plan_review.yaml   # → 1.0
```

## OpenAI Read-Only Multi-Step Execution v0 — DONE (ordered, fail-closed)

An approved read-only plan can now run **multiple allowlisted read-only steps in
order**. `src/planner/read_only_execution_gate.py` `execute_readonly_plan` runs the
plan's allowlisted steps in plan order, records `execution_order` /
`executed_skills_in_order`, runs **each step exactly once**, and **fails closed on the
first failing step** — it never retries, replans, or auto-repairs. The allowlist is
**unchanged** (`inspect_project` + `list_project_files`). A new approved, redacted
two-step fixture `fixtures/openai_planner/approved_readonly_plan_multistep/`
(`inspect_project` → `list_project_files`, ordered via `depends_on`) + eval
`evals/planner/openai_readonly_multistep_execution_gate.yaml` score **1.0** via
`scripts/run_eval.py`; the single-step evals stay **1.0**. Runner:
`scripts/run_openai_readonly_execution_gate.py --fixture multistep` (default still
`inspect_project`; fixtures restricted to `fixtures/openai_planner/`; no OpenAI call;
redacted `gate_report`). Tests:
`tests/unit/test_openai_readonly_multistep_execution.py`; wired into
`scripts/validate_workflows.py`. **No file-content read, no excluded path listed, no
browser / patch / console / server / repair / apply / merge / staging / promotion, no
raw shell, no real API call, no auto-repair, no stable promotion; stable skills /
active candidate / `safety_gate` / `promotion_policy` untouched.**

```bash
python scripts/run_openai_readonly_execution_gate.py --execute --fixture multistep
python scripts/run_eval.py --task evals/planner/openai_readonly_multistep_execution_gate.yaml   # → 1.0
```

## Read-Only Skill Allowlist Expansion v0 — DONE (list_project_files)

The read-only execution allowlist is expanded by **exactly one** safe, content-free
skill: **`list_project_files`** (now `READONLY_ALLOWLIST = ("inspect_project",
"list_project_files")`). `list_project_files` (in
`src/planner/read_only_execution_gate.py`) lists **repo-relative paths + basic metadata
only** — it reads **no file contents**, caps output at `max_files` (default 200),
**excludes** `.git/` `.venv/` `runs/` `__pycache__/` caches/build dirs, screenshots,
`.env`, `config/config.json`, `password_and_api.txt`, and secret-looking files, and
**never follows a symlink out of the repo**. All output is redacted. A new approved,
redacted fixture (`fixtures/openai_planner/approved_readonly_plan_list_files/`) + eval
(`evals/planner/openai_readonly_list_files_execution_gate.yaml`, category
`planner_readonly_execution`) score **1.0** via `scripts/run_eval.py`; the
`inspect_project` eval stays **1.0**. The runner
`scripts/run_openai_readonly_execution_gate.py` now takes `--fixture
inspect_project|list_project_files` (default `inspect_project`) and still refuses any
path outside `fixtures/openai_planner/`, makes no OpenAI call, and writes redacted
`gate_report.json/.md`. Tests: `tests/unit/test_readonly_list_project_files.py`,
`tests/unit/test_openai_readonly_list_files_eval_gate.py`; wired into
`scripts/validate_workflows.py`. **Still forbidden:** `patch_file_and_run_tests`,
`start_local_server`, `open_localhost_browser`, `read_browser_console`, repair / apply
/ merge / staging / promotion, raw-shell. No real API call, no auto-repair, no stable
promotion; stable skills / active candidate / `safety_gate` / `promotion_policy`
untouched.

```bash
python scripts/run_openai_readonly_execution_gate.py --execute --fixture list_project_files
python scripts/run_eval.py --task evals/planner/openai_readonly_list_files_execution_gate.yaml   # → 1.0
```

## OpenAI Read-Only Execution Eval Gate v0 — DONE (re-runnable; score 1.0)

The approved read-only execution flow is now a **re-runnable eval gate**.
`evals/planner/openai_readonly_execution_gate.yaml` (new orchestrator category
`planner_readonly_execution`) drives the committed APPROVED, redacted plan fixture
(`fixtures/openai_planner/approved_readonly_plan/`) through the Read-Only Plan
Execution Gate and **scores 1.0** via `scripts/run_eval.py`, asserting all 15 criteria:
`approved_plan_loaded`, `approval_marker_checked`, `reviewer_present`, `plan_valid`,
`allowlisted_skill_only`, `inspect_project_invoked`, `plan_executed_once`,
`no_patch_skill`, `no_browser_skill`, `no_console_skill`,
`no_repair_apply_merge_staging_promotion`, `no_raw_shell`, `no_secret_in_artifacts`,
`stable_safety_promotion_untouched`, `score_1_0`. The orchestrator change is **minimal
plumbing** (one dispatch branch + one handler); `safety_gate` / `promotion_policy` /
stable skills / active candidate are untouched. The allowlist is **unchanged**
(`inspect_project` only). Operator runner
`scripts/run_openai_readonly_execution_gate.py` is **dry-run by default**, `--execute`
runs the **fixture only** (must be under `fixtures/openai_planner/`), makes **no OpenAI
call**, and writes redacted `gate_report.json/.md` under the gitignored
`runs/openai_readonly_execution_gate/`. Tests:
`tests/unit/test_openai_readonly_execution_eval_gate.py`; wired into
`scripts/validate_workflows.py`. **No auto-repair, no patch/apply/merge/staging,
no stable promotion, no real API call.**

```bash
python scripts/run_openai_readonly_execution_gate.py --dry-run                    # validate only
python scripts/run_openai_readonly_execution_gate.py --execute                    # run approved fixture
python scripts/run_eval.py --task evals/planner/openai_readonly_execution_gate.yaml   # → 1.0
```

## OpenAI Read-Only Plan Execution Gate v0 — DONE (human-approved; inspect_project-only)

`src/planner/read_only_execution_gate.py` + `scripts/execute_openai_readonly_plan.py`
add a **fail-closed, human-approved gate** that runs an approved plan but executes
**only allowlisted read-only skills (v0: `inspect_project`)**. It is **dry-run by
default — nothing executes**. A REAL run requires **ALL of**: `--approved` (and not
`--dry-run`), the approval checklist line `APPROVED_FOR_READONLY_EXECUTION: true`, a
non-empty reviewer, a plan that passes `PlanValidator`, and every step an allowlisted
read-only skill. It **refuses** `patch_file_and_run_tests`, `start_local_server`,
`open_localhost_browser`, `read_browser_console`, repair / apply / merge / staging /
promotion, and `raw_shell` / `direct_command` / `exec` / `eval` / `bash` (allowlist +
denylist + per-skill runner map — three layers). It makes **no OpenAI call** (it
consumes Story 1's approved redacted plan / fixture
`fixtures/openai_planner/approved_readonly_plan/`), never replans, never auto-repairs,
never runs a shell. The `project_dir` it inspects is a **vetted operator input** —
never the model's plan inputs, browser/page content, or run traces. Results are
redacted (under the gitignored `runs/openai_readonly_plan_execution/`). Eval:
`evals/planner/openai_readonly_plan_execution.yaml`; tests:
`tests/unit/test_openai_readonly_execution_gate.py`; wired into
`scripts/validate_workflows.py`. **No patch / repair / apply / merge / staging /
stable promotion; stable skills / active candidate / `safety_gate` / `promotion_policy`
untouched.**

```bash
python scripts/execute_openai_readonly_plan.py --dry-run                          # nothing executes
python scripts/execute_openai_readonly_plan.py \
    --review-package fixtures/openai_planner/approved_readonly_plan \
    --approved --reviewer "alice" --project-dir .                                 # human-approved read-only run
```

## OpenAI Plan Review Package v0 — DONE (review-only; never executes)

`scripts/openai_plan_review.py` turns a planner plan (an OpenAI live plan, an existing
`plan.json`, or — by default — an offline deterministic fake plan) into a
**human-review package**: `plan.json`, `plan_summary.md`, `risk_assessment.md`,
`approval_checklist.md` (**NOT APPROVED BY DEFAULT / PLAN NOT EXECUTED / HUMAN APPROVAL
REQUIRED**, `APPROVED_FOR_READONLY_EXECUTION: false`), `execution_preconditions.md`,
and `review_report.json` — all redacted. The package is **REVIEW-READY** only when the
plan passes `PlanValidator`, every step is `risk_level: low`, and every step's skill is
in the read-only allowlist (v0: `inspect_project`); otherwise it is **BLOCKED** (still
produced for the record, never auto-fixed, never executed). Live packages write to the
gitignored `runs/openai_plan_review/`; a committed deterministic example +
boundaries live at
[`../reports/openai_plan_review_v0/README.md`](../reports/openai_plan_review_v0/README.md).
A real OpenAI plan needs `--real-call` + `OPENAI_API_KEY` (read only from `os.environ`
at call time; FIXED goal only); the fake provider stays the default. Tests:
`tests/unit/test_openai_plan_review.py`; wired into `scripts/validate_workflows.py`.
**Review-only**: no execution, no auto-repair, no repair/apply/merge/staging/promotion;
stable / active candidate / `safety_gate` / `promotion_policy` untouched.

```bash
python scripts/openai_plan_review.py --dry-run                                   # offline; safe anywhere
python scripts/openai_plan_review.py --plan-json runs/openai_planner_live_plan/plan.json
python scripts/openai_plan_review.py --real-call                                 # operator opt-in; one OpenAI call
```

## OpenAI Planner Live Plan-Only v0 — DONE (plan-only; dry-run default; fail-closed)

`scripts/openai_planner_live_plan.py` + `src/planner/provider_planner.py`
(`ProviderBackedPlanner.live_plan`, `parse_plan_from_text`, `LivePlanError`) let the
**OpenAI** provider generate **one real planner plan**, then validate it with
`PlanValidator`. It is strictly **plan-only**: it never executes a step, never starts
repair / apply / merge / staging / promotion, and **never auto-repairs** an invalid
plan. **Dry-run by default** (config / provider / redaction / schema check, **no API
call**); a real call needs `--real-call` **+** provider=openai **+**
`allow_real_api_calls=true` **+** `OPENAI_API_KEY` present at run time, else it **fails
closed**. Only a **FIXED system prompt + the goal** are sent — never file content,
browser/page content, or raw run traces — and a secret-looking goal is refused. A
non-JSON response or an invalid plan produces a **blocked report**; on success it
writes redacted `plan.json` / `plan_summary.md` / `planner_live_report.json` under the
gitignored `runs/openai_planner_live_plan/`. The key is read only from the named env
var at call time (config stores the NAME only) and is never printed/traced/committed.
The fake provider remains the default everywhere else. Eval (descriptive):
`evals/planner/openai_live_plan_only_blocked_or_passed.yaml`; wired into
`scripts/validate_workflows.py` (dry-run only — no real API call in the gate). No
runtime executor / stable / `safety_gate` / `promotion_policy` change. Contract:
[`../specs/planner/planner_contract.md`](../specs/planner/planner_contract.md),
[`../specs/llm/llm_provider_contract.md`](../specs/llm/llm_provider_contract.md).

```bash
python scripts/openai_planner_live_plan.py --goal "Create a safe read-only project status inspection plan. Do not execute anything." --dry-run   # safe anywhere; no API call
python scripts/openai_planner_live_plan.py --goal "Create a safe read-only project status inspection plan. Do not execute anything." --real-call  # operator opt-in; needs OPENAI_API_KEY
```

## Real Provider Planner Integration v0 — DONE (fake still default, plan-only)

The real provider runtime is now reachable through the planner via
`src/planner/provider_planner.py` (`ProviderBackedPlanner` +
`build_planner_from_config`), wired behind the fail-closed loader. **The fake
provider is still the default**; a real provider is constructed only under config
opt-in (`provider != fake` AND `allow_real_api_calls=true` AND `api_key_env`), else it
fails closed. In a **dry-run the real provider is HELD but never called** — the plan
is built deterministically from the marker. There is **no real API call** this phase
and **no real-call path** in `scripts/planner_provider_smoke.py` (dry-run only); the
planner still **only produces a plan and never executes a step**, and **no auto-repair
is started**. `scripts/plan_task.py --from-config` builds the planner from config
(fake by default, fail-closed). Eval `evals/planner/provider_backed_plan_dry_run.yaml`
→ **1.0** (`planner_provider_dry_run` category). Contract:
[`../specs/llm/llm_provider_contract.md`](../specs/llm/llm_provider_contract.md)
("Planner provider use (current)").

## Project Report v1 — available

A formal project-report draft is available at
[`../project_report/README.md`](../project_report/README.md) (12 sections: abstract,
motivation, architecture diagram, harness method, phase timeline, evaluation table,
safety, demo/dashboard, limitations, future work, conclusion, 5–8 min presentation
script). Docs-only; records the stable-promotion audit as **NO-GO / BLOCKED**; no
runtime, no real API, no stable promotion.

## Stable Promotion Readiness Audit v0 — completed (recommendation: NO-GO / BLOCKED)

A stable-promotion readiness audit is available at
[`../reports/stable_promotion_readiness_audit_v0/README.md`](../reports/stable_promotion_readiness_audit_v0/README.md):
current state, gate results, risk register, go/no-go, and the required human review.
**Audit only — no promotion performed.** Recommendation is **NO-GO / BLOCKED**:
engineering gates are green, but **stable promotion stays blocked unless all human
gates pass** (human shell-execution review, promotion-policy review, explicit operator
approval, deployed-state rollback verification). Stable / safety_gate /
promotion_policy untouched.

## Demo Package v0 — available

A single-entry showcase for presenting the project lives at
[`../demo_package/README.md`](../demo_package/README.md) (overview, architecture,
safe demo commands, dashboard, phase timeline, safety boundaries, next steps, teacher
outline). Docs-only; no runtime, no real API, no stable promotion.

## Backlog rule — one bounded story at a time

The forward work is now organized as an Epic / Story backlog under
[`../docs/epics/README.md`](../docs/epics/README.md). Going forward:

- **The next step must be chosen from
  [`../docs/epics/decision_matrix.md`](../docs/epics/decision_matrix.md)** — pick
  one story (Stable Promotion / UI Dashboard / Real Provider / Multimodal).
- **A `/goal` run executes exactly one bounded story.** No cross-story
  auto-extension; a story larger than its boundary is split, not expanded.
- **When a story is done, write a checkpoint or update a report — then stop.** Do
  not automatically begin the next story.
- Every story keeps the hard boundaries: no real API, no stable modification, no
  raw shell, no secret, untrusted content never an instruction.

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
**1.0**; `repair_propose.py` is proposal-only. Contract:
[`../specs/repair/repair_loop_contract.md`](../specs/repair/repair_loop_contract.md).

**Approved Patch Application v0 (workspace-only) is DONE.** `scripts/repair_apply.py`
takes a **human-approved** proposal and materializes the approved changes into an
**apply workspace only** — never a real target file, never stable, never a
promotion. Apply requires the `APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY` marker + a
named reviewer **and** `--approved`; without `--approved` it is rejected; it runs
only a **fixed test command allowlist** (never proposal-derived / shell).
`fake_approved_patch_application` → **1.0**. Contract:
[`../specs/repair/approved_patch_application_contract.md`](../specs/repair/approved_patch_application_contract.md);
report:
[`../reports/phase_4_approved_patch_application/README.md`](../reports/phase_4_approved_patch_application/README.md).

```bash
python scripts/repair_apply.py \
    --proposal-workspace fixtures/repair/fake_approved_proposal_workspace --dry-run   # preview, no workspace
python scripts/run_eval.py --task evals/repair/fake_approved_patch_application.yaml   # → 1.0
```

**Phase 4 (Approved Patch Application v0 — workspace-only) is complete and frozen**
at
[`../docs/checkpoints/checkpoint-phase-4-approved-patch-application.md`](checkpoints/checkpoint-phase-4-approved-patch-application.md)
(tag `checkpoint-phase-4-approved-patch-application`).

**Candidate Merge v0 (candidate-workspace-only) is DONE.** `scripts/repair_merge.py`
takes a **human-approved** apply workspace and merges its proposed changes into a
**new candidate merge workspace only** — never a real target file, an active
candidate, or stable, and never a promotion. Merge requires the
`APPROVED_FOR_CANDIDATE_MERGE` marker + a named reviewer **and** `--approved` with a
non-empty `--reviewer`; without them it is rejected; it produces a `rollback_plan.md`
and a `promotion_review_package.md` and runs only a **fixed test command allowlist**.
`fake_candidate_merge` → **1.0**. Contract:
[`../specs/repair/candidate_merge_contract.md`](../specs/repair/candidate_merge_contract.md);
report:
[`../reports/phase_5_candidate_merge/README.md`](../reports/phase_5_candidate_merge/README.md).

```bash
python scripts/repair_merge.py \
    --apply-workspace fixtures/repair/fake_approved_apply_workspace --dry-run   # preview, no workspace
python scripts/run_eval.py --task evals/repair/fake_candidate_merge.yaml        # → 1.0
```

**Phase 5 (Candidate Merge v0 — candidate-workspace-only) is complete and frozen**
at
[`../docs/checkpoints/checkpoint-phase-5-candidate-merge.md`](checkpoints/checkpoint-phase-5-candidate-merge.md)
(tag `checkpoint-phase-5-candidate-merge`).

**Human Review + Staging Promotion v0 (staging-workspace-only) is DONE.**
`scripts/staging_promote.py` takes a **human-approved** candidate merge workspace and
promotes its merged changes into a **new staging workspace only** — never a real
target file, an active candidate, or stable, and never a stable promotion. Staging
requires the `APPROVED_FOR_STAGING_PROMOTION` marker + a named reviewer **and**
`--approved` with a non-empty `--reviewer`; without them it is rejected; it verifies
the rollback plan (`rollback_verification.md`), records regression, and produces a
`stable_promotion_checklist.md`, running only a **fixed test command allowlist**.
`fake_staging_promotion` → **1.0**. Contract:
[`../specs/repair/staging_promotion_contract.md`](../specs/repair/staging_promotion_contract.md);
report:
[`../reports/phase_6_staging_promotion/README.md`](../reports/phase_6_staging_promotion/README.md).

```bash
python scripts/staging_promote.py \
    --merge-workspace fixtures/repair/fake_approved_merge_workspace --dry-run   # preview, no workspace
python scripts/run_eval.py --task evals/repair/fake_staging_promotion.yaml       # → 1.0
```

**Phase 6 (Staging Promotion v0 — staging-workspace-only) is complete and frozen**
at
[`../docs/checkpoints/checkpoint-phase-6-staging-promotion.md`](checkpoints/checkpoint-phase-6-staging-promotion.md)
(tag `checkpoint-phase-6-staging-promotion`). **Stable promotion is not started.**

## Decision point — next phase (none started)

**Planning-only stories completed (no runtime built):** UI dashboard
([`story_ui_dashboard_v0`](../docs/epics/stories/story_ui_dashboard_v0.md),
[`../docs/ui_dashboard/`](../docs/ui_dashboard/)), real provider
([`story_real_provider_v0`](../docs/epics/stories/story_real_provider_v0.md),
[`../docs/real_provider/`](../docs/real_provider/)), and multimodal / data channels
([`story_multimodal_channel_v0`](../docs/epics/stories/story_multimodal_channel_v0.md),
[`../docs/multimodal_data_channels/`](../docs/multimodal_data_channels/)). Each is a
planning gate only; a real build of any is a separate, later gated story that must add
+ pass its own evals first.

The remaining substantive option:

- **Stable Promotion — REMAINS BLOCKED** behind a human / policy / rollback /
  shell-review gate. A human reviews a staging workspace + its stable-promotion
  checklist, confirms the verified rollback and full regression, completes the human
  shell-execution review, then the promotion policy moves a candidate to `stable`.
  **Stable promotion not started.** Hard prerequisites:
  - **Must NOT modify stable directly** (no automated/silent stable write).
  - **A human must review** the staging workspace + stable-promotion checklist.
  - **Must confirm the verified rollback** before promotion.
  - **Must run full regression** before stable.
  - **Must complete the human shell-execution review** (per the promotion policy).
  - **Must follow the promotion policy** (`specs/harness/promotion_policy.md`).
  - **Must preserve the stable / safety_gate / promotion_policy invariant.**

A future build story (UI / real provider / multimodal) may also be chosen, but each
remains planning-gated until its own evals exist and pass.

**UI Dashboard Skeleton v0 — DONE (read-only).** A read-only static dashboard
skeleton (`ui_dashboard/`) + snapshot generator
(`scripts/generate_dashboard_snapshot.py`, reads only redacted docs, refuses on
secret) + validator (`scripts/validate_dashboard.py`, wired into validate_workflows)
now exist. It visualizes status only — **still no action execution**: no repair /
apply / merge / staging / promotion trigger, no raw shell, no API call, no secret
display. Any real action remains a human terminal step through the existing
approval-gated scripts. Report:
[`../reports/story_ui_dashboard_skeleton_v0/README.md`](../reports/story_ui_dashboard_skeleton_v0/README.md).

**UI Dashboard Real-Browser Smoke Gate v0 — DONE (read-only).** A real-browser smoke
gate (`scripts/run_dashboard_smoke.py`, `evals/dashboard/ui_dashboard_readonly_smoke.yaml`)
loads the dashboard in a real Playwright browser from an in-process localhost static
server and verifies it stays read-only — no button/form/onclick/POST, no external
request, no secret, no action trigger — then tears down with no lingering process
(`score=1.0`; `--dry-run` safe anywhere). **Still no action execution.** Report:
[`../reports/story_ui_dashboard_smoke_v0/README.md`](../reports/story_ui_dashboard_smoke_v0/README.md).

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
