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
