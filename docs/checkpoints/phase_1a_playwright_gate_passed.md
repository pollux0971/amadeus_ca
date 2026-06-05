# Phase 1A — Playwright Real-Browser Gate PASSED (Branch B applied)

The Playwright real-browser gate passed and **Branch B has been applied**:
`open_localhost_browser_v1` is now **staging-ready**. `read_browser_console`
remains blocked (next to implement); the full browser gate stays blocked.

## Result

- **timestamp (applied):** 2026-06-05T22:58:04Z
- **referenced setup report:** `phase_1a_playwright_environment_setup_report.md`
  (and readiness note `phase_1a_playwright_gate_ready_for_branch_b.md`).
- **gate:** `scripts/run_playwright_gate.py` → exit 0 (PASS).
- **eval:** `open_localhost_playwright_required_smoke` → **score = 1.0** (all 10
  criteria pass).
- **engine = playwright**
- **is_real_browser = true**
- `screenshot_supported = true`, `js_supported = true`, `console_supported = true`
- score metrics: `browser_engine=playwright`, `browser_is_real=true`.

## Artifact refs (gate run)

- run dir: `runs/open_localhost_playwright_required_smoke_*` (`score.json`,
  `trace.jsonl`, `summary.md`, `task.yaml`).
- browser artifacts (ephemeral temp dir; not committed — regenerate by re-running
  the gate):
  - `result.json` — `status=loaded`, `engine=playwright`, `is_real_browser=true`,
    `status_code=200`, `title="Keep-Alive Demo"`.
  - `page_snapshot.json` — real localhost URL + `{links:1, buttons:2, forms:1}`.
  - `screenshot.png` — real rendered PNG, **1280×720**.

## No lingering process

Precise check (`ms-playwright|headless_shell|chrome-linux64/chrome|node server.js|http.server`):
**none** ✅. (Host has the operator's pre-existing desktop Chrome, unrelated and
untouched.)

## Branch B applied — official status changes

- `harnesses/candidates/open_localhost_browser_v1/candidate.yaml`:
  `status: dev → staging-ready` (metadata only; `active`/`version`/runtime code
  unchanged).
- `docs/candidate_status_matrix.md`: row → **staging-ready**, E2E → real-browser
  gate 1.0, Playwright blocker removed.
- `docs/promotion_readiness_review.md`: verdict → **staging-ready after the
  real-browser gate** (with the gate capability flags recorded).
- `docs/next_milestone_plan.md`: Step 1 marked **completed**; next =
  `read_browser_console_v1`.
- `docs/quick_resume.md`: `open_localhost_browser_v1` staging-ready; next step
  `read_browser_console_v1`.

## Still blocked / not done (by design)

- `open_localhost_browser_v1` is **staging-ready**, not `stable` — promotion to
  `staging` is an operator decision.
- **read_browser_console is blocked** — no candidate yet; it is the **next** thing
  to implement and **must force `browser_mode=playwright`**.
- **full_browser_vite_login_bug_e2e** stays draft/blocked; `run_full_browser_gate.py`
  was **NOT** run (no console candidate).
- **http_fallback is not a real browser** — still true for the fallback engine.

## Invariants

- stable skills / safety_gate / promotion_policy **untouched**.
- No runtime code changed (only candidate.yaml metadata + docs + validator/tests).
- The Branch B draft pack is retained as history.

## Next recommended step

Start `read_browser_console_v1` (forcing `browser_mode=playwright`); build a
console smoke eval first, then proceed to the full browser e2e via
`scripts/run_full_browser_gate.py`.
