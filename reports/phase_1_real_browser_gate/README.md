# Phase 1 — Real-Browser Gate (report)

Stage report for the real-browser milestone. Continues from the 0→1 MVP
(`../phase_0_to_1_harness_mvp/`).

## Outcome

- **Playwright real-browser gate PASSED.** In a Playwright + Chromium environment,
  `python scripts/run_playwright_gate.py` ran
  `evals/browser/open_localhost_playwright_required_smoke.yaml` to **score 1.0**
  with `engine=playwright`, `is_real_browser=true`, JS/console/screenshot
  supported, a real 1280×720 screenshot + page snapshot, and no lingering process.
- **Branch B applied:** `open_localhost_browser_v1` is now **staging-ready**.
- Evidence:
  - `../../docs/checkpoints/phase_1a_playwright_environment_setup_report.md`
  - `../../docs/checkpoints/phase_1a_playwright_gate_passed.md`

## Environment note

Playwright + Chromium were installed into an isolated project `.venv`
(operator-approved; no sudo, no global install, no `install-deps`). The
`.venv`, the ms-playwright browser cache, runs, and screenshot binaries are
**not committed**.

## Progress

1. ✅ **`read_browser_console_v1`** — implemented. Real Playwright console
   collector that **forces `browser_mode=playwright`**, rejects `http_fallback`
   (`http_fallback_not_allowed`), and fails with `browser_runtime_missing` when
   Playwright is absent — never a fabricated console (ADR-013). The console smoke
   `read_browser_console_smoke` scores **1.0** in a Playwright environment
   (`engine=playwright`, `console_supported=true`, correct console counts;
   `console_log.json` + `result.json` produced).

## Next phase

2. **`full_browser_vite_login_bug_e2e`** — still **blocked / not run**. A
   `read_browser_console` candidate now exists, but the full chain (criteria
   evidence rules for `patch_applied` / `browser_reverify_passed` /
   `no_fatal_console_error_after_patch` + the post-patch re-verify flow) is **not
   yet wired**. `scripts/run_full_browser_gate.py` is **not run** this round.

## Still true

- **http_fallback is not a real browser** — the fallback engine remains a smoke
  only; real-browser work uses the Playwright engine.
- stable skills / safety_gate / promotion_policy untouched.
