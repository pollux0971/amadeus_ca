# DRAFT patch — docs/promotion_readiness_review.md

> ⚠️ **DRAFT. This is not automatically applied and is not the current verdict.**
> Apply by hand only after the Playwright gate passes (see `branch_b_apply_checklist.md`).

## Replace section 3 (open_localhost_browser_v1)

**Current verdict (unchanged until the gate passes):** keep `dev` until the
Playwright gate is green.

**Proposed verdict (after the gate passes):**

> ## 3. open_localhost_browser_v1 — **staging-ready after the real-browser gate**
>
> - The real Playwright browser gate has **passed**:
>   `open_localhost_playwright_required_smoke` scored 1.0 with `engine=playwright`,
>   `is_real_browser=true`, and `screenshot/js/console_supported=true`.
> - **Gate artifact requirements (must all be present in the gate run):** a
>   `result.json` with the capability flags above, a `page_snapshot.json`, a
>   `screenshot.png`, and a run with **no lingering server/browser process**.
> - The score is recorded honestly: `browser_engine=playwright`,
>   `browser_is_real=true` in the run metrics.
> - Verdict: **staging-ready.** Promote to `staging` on operator approval (the
>   browser-runtime surface is a real runtime, reviewed like shell execution);
>   `stable` remains a separate, later decision.

## Keep section 4 (read_browser_console) unchanged

`read_browser_console` **stays blocked until its candidate is created**. Passing
the browser gate only unblocks *starting* `read_browser_console_v1` (which must
force `browser_mode=playwright`); it does not promote or create a console skill.
