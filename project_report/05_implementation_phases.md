# 05 — Implementation Phases

## Phase timeline

| Phase / item | Outcome | Gate | Checkpoint / tag |
|---|---|---|---|
| **Phase 1B — full real-browser e2e** | `full_browser_vite_login_bug_e2e` 1.0 (start → real browser → console → patch+tests → re-open → console; fatal=0) | real Playwright browser | `checkpoint-phase-1b-full-browser-e2e` |
| **Phase 2A — fake planner execution bridge** | `fake_full_browser_plan_execution` 1.0; validated fake plan → allowlisted skills | execution bridge (allowlist + approval, no replan) | `checkpoint-phase-2a-fake-planner-execution` |
| **Phase 3 — repair proposal-only** | `fake_repair_proposal_only` 1.0; failure → proposal in candidate workspace | proposal-only; `--apply` rejected | `checkpoint-phase-3-repair-proposal-only` |
| **Phase 4 — approved patch application** | `fake_approved_patch_application` 1.0; approved → apply workspace only | human approval marker + reviewer + `--approved` | `checkpoint-phase-4-approved-patch-application` |
| **Phase 5 — candidate merge** | `fake_candidate_merge` 1.0; → candidate merge workspace + rollback plan + promotion review package | human approval + reviewer | `checkpoint-phase-5-candidate-merge` |
| **Phase 6 — staging promotion** | `fake_staging_promotion` 1.0; → staging workspace + rollback verification + stable checklist | human approval + reviewer; rollback verified | `checkpoint-phase-6-staging-promotion` |
| **Epics / Stories backlog** | `docs/epics/` (4 epics, stories, decision matrix); one bounded story per `/goal` | `validate_epics` | — |
| **UI dashboard skeleton** | read-only `ui_dashboard/` + snapshot generator + validator | `validate_dashboard` | report `reports/story_ui_dashboard_skeleton_v0/` |
| **UI dashboard real-browser smoke gate** | `ui_dashboard_readonly_smoke` 1.0; no external request; no lingering process | `run_dashboard_smoke.py` (Playwright) | report `reports/story_ui_dashboard_smoke_v0/` |
| **Demo package** | single-entry showcase (`demo_package/`) | `validate_demo_package` | report `reports/demo_package_v0/` |
| **Stable promotion readiness audit** | **NO-GO / BLOCKED** | `validate_stable_promotion_audit` | report `reports/stable_promotion_readiness_audit_v0/` |

## The self-evolution components

- **Fake provider** (`src/llm/`) — offline, deterministic, fail-closed; no real API.
- **Fake planner** (`src/planner/`) — marker → declarative plan; validated.
- **Execution bridge** — runs only allowlisted skills, with approval; no replan.
- **Repair proposal** — failure → declarative proposal in a candidate workspace.
- **Apply workspace** — approved proposal materialized into an apply workspace only.
- **Candidate merge workspace** — merged change + rollback plan + promotion review.
- **Staging workspace** — staged change + rollback verification + stable checklist.

## One-line shape

```
real-browser e2e (1B) → fake planner execution (2A)
  → repair proposal (3) → approved apply (4) → candidate merge (5) → staging (6)
  → [BLOCKED] stable promotion
+ Epic/Story backlog · read-only dashboard (+ smoke gate) · demo package · stable audit (NO-GO)
```

Throughout: stable skills / active candidate runtime / safety_gate / promotion_policy
**untouched**; no real API; no secret committed.
