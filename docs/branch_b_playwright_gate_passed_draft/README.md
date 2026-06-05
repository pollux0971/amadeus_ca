# Branch B draft — apply ONLY after the Playwright gate passes

> ⚠️ **This is a Branch B draft. It is NOT the current status and must NOT be
> applied automatically.** These files describe the changes to make *after* the
> `open_localhost_browser_v1` real-browser gate passes. Until then they are
> inert reference text. **Do not apply.**

As of now (Phase 1A), the gate has **not** passed — this environment has no
Playwright/Chromium (see `../checkpoints/phase_1a_playwright_gate_attempt.md`).
So `open_localhost_browser_v1` stays `dev` and `read_browser_console` stays
blocked.

## Trigger condition (all must hold before applying Branch B)

Apply these drafts only when `python scripts/run_playwright_gate.py` (the real,
non-dry-run gate) has passed with:

- eval `open_localhost_playwright_required_smoke` **score = 1.0**
- `engine=playwright`
- `is_real_browser=true`
- `screenshot_supported=true`
- `js_supported=true`
- `console_supported=true`
- a screenshot artifact and a page_snapshot artifact exist
- **no lingering server/browser process**

See `branch_b_apply_checklist.md` for the full pre-apply checklist (including
operator approval).

## Contents (all drafts — do not apply)

| File | What it drafts |
|---|---|
| `candidate_status_matrix.patch.md` | open_localhost_browser_v1 → staging-ready in the matrix |
| `promotion_readiness_review.patch.md` | open_localhost_browser_v1 verdict → staging-ready after real-browser gate |
| `next_milestone_plan.patch.md` | mark Playwright gate completed; next = read_browser_console_v1 |
| `quick_resume.patch.md` | quick_resume reflects staging-ready + next step |
| `read_browser_console_v1_planning_note.md` | minimum requirements for the future console skill (planning only) |
| `branch_b_apply_checklist.md` | the human pre-apply checklist |

## Not in scope of this draft

- No candidate `candidate.yaml` `active/status/stage` is changed.
- No `read_browser_console` implementation — only a planning note.
- No real gate run, no install, no full browser gate.
