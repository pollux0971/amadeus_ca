# DRAFT patch — docs/next_milestone_plan.md

> ⚠️ **DRAFT. This is not automatically applied and does not change the current
> order.** Apply by hand only after the Playwright gate passes (see
> `branch_b_apply_checklist.md`).

## Mark Step 1 (Playwright gate) completed

**Proposed:** annotate Step 1 as done:

> 1. ✅ **Playwright real-browser gate — COMPLETED.**
>    `python scripts/run_playwright_gate.py` passed: score 1.0, `engine=playwright`,
>    `is_real_browser=true`, screenshot + snapshot artifacts, no lingering process.

And Step 2:

> 2. ✅ `open_localhost_browser_v1` marked **staging-ready** (real-browser gate green).

## Make the next active step read_browser_console_v1

**Proposed:** the next actionable step becomes:

> ### Next: Start `read_browser_console_v1`
> Now unblocked. The candidate **must force `browser_mode=playwright`** and fail
> with `browser_runtime_missing` when Playwright is absent — never a fabricated
> console (ADR-013). Build a console **smoke eval** first; then proceed to the
> full browser e2e.

## Full browser gate still gated on the console candidate

**Unchanged:** `full_browser_vite_login_bug_e2e` and
`scripts/run_full_browser_gate.py` stay **blocked** until a `read_browser_console`
candidate exists. Do **not** run the full browser gate before then.

> The remaining order (read_browser_console_v1 → full_browser e2e → planner/UI)
> is unchanged; only Step 1/2 flip to completed.
