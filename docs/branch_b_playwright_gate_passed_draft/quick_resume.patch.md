# DRAFT patch — docs/quick_resume.md

> ⚠️ **DRAFT. This is not automatically applied and is not the current resume
> state.** Apply by hand only after the Playwright gate passes (see
> `branch_b_apply_checklist.md`).

## Update "What is blocked" → open_localhost_browser line

**Current:** "open_localhost_browser_v1 stays `dev`. http_fallback is not a real
browser …"

**Proposed (after the gate passes):**

> - `open_localhost_browser_v1` is **staging-ready** — the Playwright real-browser
>   gate passed (`engine=playwright`, `is_real_browser=true`). It is no longer
>   blocked from staging (operator approval still required to actually promote).

## Update active overrides note / next step

**Proposed next-step line:**

> **Next step:** start `read_browser_console_v1` (must force
> `browser_mode=playwright`). The **full browser gate remains blocked until a
> `read_browser_console` candidate exists** — do not run it before then.

## Keep unchanged

- `read_browser_console` is still **blocked** until its candidate is created.
- Do not run the full browser gate yet.
- **http_fallback is not a real browser** (still true for the fallback path).
