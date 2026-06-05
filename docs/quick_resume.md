# Quick Resume (read me first when coming back)

One-minute orientation. For detail see
[`candidate_status_matrix.md`](candidate_status_matrix.md),
[`promotion_readiness_review.md`](promotion_readiness_review.md), and
[`next_milestone_plan.md`](next_milestone_plan.md).

**Latest checkpoint:**
[`checkpoints/checkpoint-0-to-1-harness-gates.md`](checkpoints/checkpoint-0-to-1-harness-gates.md)
— frozen status + handoff note.

**Phase report:**
[`../reports/phase_0_to_1_harness_mvp/README.md`](../reports/phase_0_to_1_harness_mvp/README.md)
— overview, architecture, demos, diagrams, results, risks, next-phase plan.

Branch B draft (apply only after the Playwright gate passes — not current status) exists at [`branch_b_playwright_gate_passed_draft/`](branch_b_playwright_gate_passed_draft/README.md).

**Progress log:** [`progress_log.md`](progress_log.md) — chronological status + verified health.

## Current active overrides

The harness overlay resolver currently activates these candidates (highest
active version per overridden skill):

```text
open_localhost_browser     -> open_localhost_browser_v1
patch_file_and_run_tests   -> patch_file_and_run_tests_v2
start_local_server         -> start_local_server_v1   (release 1.2)
```

`read_browser_console` has **no candidate** — it runs the stable placeholder and
is intentionally **blocked** from getting one yet.

## What is green now

- `python scripts/run_demo.py --demo vite_login_bug` → **1.0**
  (real server keep_alive + http_fallback browser load + real patch).
- `python scripts/run_eval.py --task evals/browser/open_localhost_keep_alive_smoke.yaml` → **1.0**
  (but `browser_engine=http_fallback`, `browser_is_real=false`).
- `python scripts/run_eval.py --task evals/patch_runner/py_calc_bug_e2e.yaml` → **1.0**.
- `python scripts/run_unit_tests.py` → all pass. `validate_structure` /
  `validate_workflows` / `run_skill_tests` pass.
- No lingering server/browser processes after runs; the `_sessions` registry is
  empty after a clean run.

## What is blocked

- **read_browser_console is blocked.** Do not start it yet. It must depend on
  `browser_mode=playwright`; a console on the http_fallback would be fake (ADR-013).
  **This is the next step to implement** (`read_browser_console_v1`).
- **open_localhost_browser_v1 is `staging-ready`.** The Playwright real-browser
  gate PASSED (`engine=playwright`, `is_real_browser=true`) — Branch B applied.
  The http_fallback path is still a smoke only (**http_fallback is not a real
  browser**); promote to `staging` on operator approval.
- **full_browser_vite_login_bug_e2e is draft / blocked.** Its gate runner refuses
  to run until a `read_browser_console` candidate exists. **Do not run the full
  browser gate yet.**
- `patch_file_and_run_tests_v2` is staging-ready but needs a human shell-execution
  review before `stable`.

**Next step:** start `read_browser_console_v1` (must force `browser_mode=playwright`).

## Dry-run gate commands (safe anywhere — no browser, no install)

```bash
python scripts/run_playwright_gate.py --dry-run
python scripts/run_full_browser_gate.py --dry-run
```

## What NOT to do yet

- Do not install Playwright / Chromium as part of this repo.
- **Do not run the full browser gate** (`python scripts/run_full_browser_gate.py`)
  until Playwright + Chromium + a `read_browser_console` candidate all exist.
- Do not run `python scripts/run_playwright_gate.py` (non-dry-run) unless
  Playwright + Chromium are installed.
- Do not start `read_browser_console`.
- Do not add a scheduled reaper / cron / loop.
- Do not modify stable skills, `safety_gate`, or `promotion_policy`.

## Exact next real step (when a Playwright environment is available)

1. In an env with Playwright + Chromium (`pip install playwright && playwright
   install chromium`), run:
   ```bash
   python scripts/run_playwright_gate.py
   ```
   It must score 1.0 with `is_real_browser=true`.
2. If it passes → mark `open_localhost_browser_v1` staging-ready (update its
   `candidate.yaml` / status docs).
3. Then build `read_browser_console_v1`, forcing `browser_mode=playwright`.
4. Finally run `python scripts/run_full_browser_gate.py` for the full chain.
