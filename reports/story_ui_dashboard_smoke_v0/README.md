# Story Execution Report — UI Dashboard Real-Browser Smoke Gate v0

**Story:** UI Dashboard Real-Browser Smoke Gate v0 (EPIC-UI) · **Result:** ✅
completed — dashboard smoke **score 1.0** on a real Playwright browser.

## What this story did

Added a **read-only** real-browser smoke gate for the dashboard skeleton. The gate:
generate snapshot → validate dashboard → start an **in-process** localhost static
server (no subprocess/shell) → open the dashboard in a **real Playwright browser** →
verify the read-only UI → teardown browser + server → assert **no lingering process**.
It adds **no action surface** of any kind.

## Changed files summary

- **Added** `evals/dashboard/ui_dashboard_readonly_smoke.yaml` (19 success criteria).
- **Added** `scripts/run_dashboard_smoke.py` (`--dry-run` safe anywhere; real run
  needs Playwright via `.venv`; in-process `http.server`, no subprocess/shell).
- **Added** `tests/unit/test_dashboard_smoke_gate.py`,
  `reports/story_ui_dashboard_smoke_v0/README.md`.
- **Extended** `scripts/validate_dashboard.py` (now also requires the smoke eval +
  runner, the read-only/teardown criteria, and a shell-free runner with `--dry-run`)
  — already wired into `scripts/validate_workflows.py`.
- **Updated** `ui_dashboard/README.md`, `docs/quick_resume.md`,
  `docs/next_milestone_plan.md`, `reports/story_ui_dashboard_skeleton_v0/README.md`.
  No runtime `src/` change.

## Smoke flow result (real browser, via `.venv`)

`python scripts/run_dashboard_smoke.py` → **`ui_dashboard_readonly_smoke` score=1.0**
(19/19). Verified: snapshot generated; dashboard validated; page loaded; title /
heading / latest checkpoint / phase status / eval status visible; snapshot visible;
**no_button / no_form / no_onclick / no_post_action**; **no_external_request** (only
127.0.0.1); **no_secret_in_body**; **no_action_trigger**; **browser_teardown /
server_teardown / no_lingering_process**.

## Validation summary

- `validate_structure` PASS · `validate_workflows` PASS (incl. dashboard + smoke
  gate) · `check_secret_hygiene` exit 0 · `validate_config` PASS ·
  `llm_smoke --fake-only` → fake.
- `generate_dashboard_snapshot` OK · `validate_dashboard` PASS ·
  `run_dashboard_smoke --dry-run` safe · `run_dashboard_smoke` (.venv) **1.0** ·
  `run_full_browser_gate --dry-run` safe · `run_demo vite_login_bug` 1.0 ·
  `run_skill_tests` 5/5 · `run_unit_tests` all pass.

## Acceptance criteria

- [x] dashboard real-browser smoke eval exists
- [x] `run_dashboard_smoke.py` exists
- [x] dashboard smoke score = 1.0
- [x] dashboard loads in a real Playwright browser
- [x] snapshot visible
- [x] no action-execution UI (no button/form/onclick/POST/action trigger)
- [x] no secret display
- [x] no external fetch (only localhost)
- [x] no lingering server/browser process
- [x] validate_workflows includes dashboard smoke validation

## Remaining risks

- The real run requires Playwright + Chromium (`.venv`); under the system interpreter
  the gate `--dry-run` is safe and the unit test skips the live run. This mirrors the
  existing real-browser gates.
- The smoke asserts read-only properties at load; the dashboard remains a skeleton
  with no action surface by design.

## Next decision point

Per [`../../docs/epics/decision_matrix.md`](../../docs/epics/decision_matrix.md):
**Stable Promotion remains blocked** behind human / policy / rollback / shell-review
gates. Further UI work stays read-only and gated.

## Definition of Done

Acceptance criteria met; validation green; smoke gate at 1.0 on a real browser; no
lingering process; read-only (no action surface); working tree clean; **stop**.
