# DRAFT patch — docs/candidate_status_matrix.md

> ⚠️ **DRAFT. This is not automatically applied and is not the current status.**
> Apply by hand only after the Playwright gate passes (see `branch_b_apply_checklist.md`).

## Change the `open_localhost_browser_v1` row

**Current (do not change until the gate passes):**

```text
| `open_localhost_browser_v1` | open_localhost_browser | `true` | 1 | **dev** (blocked from staging) | candidate + e2e unit tests pass | `open_localhost_keep_alive_smoke` 1.0 **via http_fallback** (`is_real_browser=false`) | no Playwright/Chromium here → not a real browser; **real-browser gate eval + runner exist but not yet executed in a Playwright environment** (`scripts/run_playwright_gate.py`) | Keep `dev`. **Not staging** until the real-browser (Playwright) e2e in `playwright_verification_plan.md` passes. |
```

**Proposed (after the gate passes):**

```text
| `open_localhost_browser_v1` | open_localhost_browser | `true` | 1 | **staging-ready** | candidate + e2e unit tests pass | **real-browser gate `open_localhost_playwright_required_smoke` 1.0** (`engine=playwright`, `is_real_browser=true`) | none for the browser smoke; `read_browser_console` is a separate, still-blocked track | Promote to `staging` on operator approval (shell/browser-runtime review per promotion policy); `read_browser_console` still blocked until its candidate is created. |
```

## Keep this row unchanged

```text
| `read_browser_console_not_started` | read_browser_console | n/a (no candidate yet) | — | **blocked** | n/a | n/a | requires `browser_mode=playwright` (real browser); blocked until implementation starts | **Do not start** until a `read_browser_console_v1` candidate is created. |
```

`read_browser_console_not_started` **stays blocked** — passing the browser gate
unblocks *starting* the console candidate, it does not create or unblock the
console skill itself.
