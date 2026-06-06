# 09 · Next Phase Plan

> **Update (after this report):** Phase **1A** (Playwright real-browser gate) and
> Phase **1B** (full real-browser e2e) are **COMPLETE** — all three gates are green
> (Playwright gate 1.0, console smoke 1.0, `full_browser_vite_login_bug_e2e` 1.0).
> See `../phase_1_real_browser_gate/README.md` and
> `../../docs/checkpoints/checkpoint-phase-1b-full-browser-e2e.md`. The next
> milestone is **no longer the Playwright gate** — it is a product decision point
> (LLM planner / auto-repair loop / UI / multimodal), tracked in
> `../../docs/next_milestone_plan.md`. The steps below are the original plan, kept
> for history.

Ordered next steps. The gates are intentional — **do not skip them.**

## Entry: Playwright real browser gate

1. In an environment with Playwright + Chromium
   (`pip install playwright && playwright install chromium`), run:
   ```bash
   python scripts/run_playwright_gate.py --dry-run   # safe anywhere
   python scripts/run_playwright_gate.py             # only with Playwright + Chromium
   ```
   It runs `evals/browser/open_localhost_playwright_required_smoke.yaml` and must
   score **1.0** with `is_real_browser=true` (engine=playwright, JS/console/
   screenshot supported, a screenshot artifact, no lingering server).

## After the gate passes

2. **Mark `open_localhost_browser_v1` staging-ready** — only after the real-browser
   gate is green (record `engine=playwright`, `is_real_browser=true`).
3. **Build `read_browser_console_v1`** — only now is it unblocked. It **must force
   `browser_mode=playwright`** and fail with `browser_runtime_missing` when
   Playwright is absent (never a fabricated console).
4. **Run `full_browser_vite_login_bug_e2e`** via
   `python scripts/run_full_browser_gate.py` — the full chain (start_local_server
   keep_alive → real browser → read_browser_console → patch → rerun/verify). The
   runner refuses to run until the Playwright gate has passed **and** a
   `read_browser_console` candidate exists.

## Later (only after the browser path is real)

5. Consider an **LLM planner** to replace rule-based step selection.
6. Consider a **Claude Code / Codex auto-repair loop** (read failure_report →
   propose candidate → eval → promotion).
7. Consider **UI** (the `apps/` surface), **multimodal**, and **data channels** —
   each via the brownfield intake → manifest → adapter → eval → promotion path.

## Gates not to skip

- **Do not** treat the HTTP fallback as a real browser.
- **Do not** start `read_browser_console` before the Playwright gate passes.
- **Do not** run the full browser gate before Playwright + Chromium + a console
  candidate exist.
- **Do not** promote shell-executing candidates to `stable` without a human
  review.
- **Do not** modify stable skills, `safety_gate`, or `promotion_policy` outside
  the candidate + promotion workflow.
