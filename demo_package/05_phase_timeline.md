# 05 — Phase Timeline

Each entry: outcome · gate · checkpoint/tag (where the repo records one) · remaining
risk. Checkpoints live in `docs/checkpoints/`; reports in `reports/`.

| Phase / item | Outcome | Gate | Checkpoint / tag | Remaining risk |
|---|---|---|---|---|
| **Phase 1B — full real-browser e2e** | `full_browser_vite_login_bug_e2e` 1.0 (start → real browser → console → patch+tests → re-open → console; fatal=0) | real Playwright browser via `run_full_browser_gate.py` | `checkpoint-phase-1b-full-browser-e2e` | needs Playwright/Chromium (.venv); http_fallback is not a real browser |
| **Phase 2A — fake planner execution bridge** | `fake_full_browser_plan_execution` 1.0; validated plan → allowlisted skills | execution bridge (allowlist + approval, no replan) | `checkpoint-phase-2a-fake-planner-execution` | markers are deterministic, not semantic planning |
| **Phase 3 — repair proposal-only** | `fake_repair_proposal_only` 1.0; failure → proposal in candidate workspace | proposal-only; `--apply` rejected | `checkpoint-phase-3-repair-proposal-only` | no apply; human review required |
| **Phase 4 — approved patch application** | `fake_approved_patch_application` 1.0; approved → apply workspace only | human approval marker + reviewer + `--approved` | `checkpoint-phase-4-approved-patch-application` | no merge; no promotion |
| **Phase 5 — candidate merge** | `fake_candidate_merge` 1.0; → candidate merge workspace + rollback plan + promotion review package | human approval + reviewer | `checkpoint-phase-5-candidate-merge` | no staging/stable promotion |
| **Phase 6 — staging promotion** | `fake_staging_promotion` 1.0; → staging workspace + rollback verification + stable checklist | human approval + reviewer; rollback verified | `checkpoint-phase-6-staging-promotion` | **stable promotion blocked** behind human/policy/rollback/shell-review |
| **Epics / Stories backlog** | `docs/epics/` (4 epics, stories, decision matrix); one bounded story per `/goal` | `validate_epics` | (no tag; in `docs/epics/`) | planning epics await build stories with their own evals |
| **UI dashboard skeleton** | read-only `ui_dashboard/` + snapshot generator + validator | `validate_dashboard` | report `reports/story_ui_dashboard_skeleton_v0/` | skeleton only; no action surface |
| **UI dashboard real-browser smoke gate** | `ui_dashboard_readonly_smoke` 1.0 in a real browser; no external request; no lingering process | `run_dashboard_smoke.py` (Playwright) | report `reports/story_ui_dashboard_smoke_v0/` | needs Playwright (.venv) for the real run |

## One-line shape

```
real-browser e2e (1B)
  → fake planner execution (2A)
  → repair proposal (3) → approved apply (4) → candidate merge (5) → staging (6)
  → [BLOCKED] stable promotion
+ Epic/Story backlog · read-only dashboard · dashboard smoke gate
```

Throughout: **stable skills / active candidate runtime / safety_gate /
promotion_policy untouched**; no real API; no secret committed.
