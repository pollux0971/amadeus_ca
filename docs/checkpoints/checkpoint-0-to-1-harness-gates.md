# Checkpoint: 0→1 Harness + Gate Chain

Frozen status snapshot at the end of the candidate-build + gate-scaffolding
stage. This is a **handoff note** — read it (plus
[`../quick_resume.md`](../quick_resume.md)) to resume work from exactly here.
No runtime code, stable skill, `safety_gate`, or `promotion_policy` is part of
this checkpoint; it is documentation only.

## Headline

The 0→1 walking skeleton is complete and several skills have real candidate
implementations. The remaining frontier is the **real browser path**, which is
deliberately gated and not yet executed (no Playwright/Chromium in this env).

## Completed

- **Walking skeleton — done.** Eval task → skill registry → candidate overlay →
  skill execution → `trace.jsonl` → `score.json` runs end to end via the
  orchestrator and `scripts/run_eval.py` / `scripts/run_demo.py`.

## Candidate status (frozen)

| Candidate | Stage | Notes |
|---|---|---|
| `patch_file_and_run_tests_v2` | **staging-ready after human shell review** | data-driven (replace_text / unified_diff), sandbox copy; v1 superseded (`active:false`, not deleted). |
| `start_local_server_v1.2` | **dev / staging-candidate** | real subprocess lifecycle + **keep_alive** + idempotent **teardown** + **lease reaper** (`scripts/reap_server_sessions.py`); lease is advisory, not an OS-level watchdog. |
| `open_localhost_browser_v1` | **dev** | consumes the kept-alive `server_url`; **http_fallback smoke = 1.0** but **http_fallback is not a real browser** (`engine=http_fallback`, `is_real_browser=false`). |
| `read_browser_console` | **blocked** | no candidate; must wait for `browser_mode=playwright`. **read_browser_console blocked.** |

## Gates (frozen)

- **Playwright real-browser gate** — `scripts/run_playwright_gate.py` +
  `evals/browser/open_localhost_playwright_required_smoke.yaml` **exist but have
  NOT been executed** (no Playwright/Chromium here). `--dry-run` is safe.
- **Full browser e2e gate** — `scripts/run_full_browser_gate.py` +
  `evals/browser/full_browser_vite_login_bug_e2e.yaml` (`draft: true`,
  `blocked_until: playwright_gate_passed_and_console_skill_exists`) **exist but
  are blocked**; the runner refuses to run (exit 2) until the Playwright gate has
  passed AND a `read_browser_console` candidate exists.

## Active overrides at this checkpoint

```text
open_localhost_browser     -> open_localhost_browser_v1
patch_file_and_run_tests   -> patch_file_and_run_tests_v2
start_local_server         -> start_local_server_v1   (release 1.2)
```

## Green at this checkpoint

- `run_demo.py --demo vite_login_bug` → **1.0**
- `run_eval.py --task evals/browser/open_localhost_keep_alive_smoke.yaml` → **1.0**
  (`browser_engine=http_fallback`, `browser_is_real=false`)
- `run_eval.py --task evals/patch_runner/py_calc_bug_e2e.yaml` → **1.0**
- `validate_structure` / `validate_workflows` / `run_skill_tests` / `run_unit_tests`
  all pass; both gate runners are safe under `--dry-run`.
- No lingering server/browser processes; `_sessions` registry empty after runs.

## Invariants preserved

- **stable skills / safety_gate / promotion_policy untouched** throughout.
- All candidate work lives under `harnesses/candidates/`; the harness overlay
  resolver activates the highest active version per skill.

## Resume from here

1. One-minute orientation: [`../quick_resume.md`](../quick_resume.md).
2. Next real step requires a Playwright + Chromium environment, then:
   `python scripts/run_playwright_gate.py` (must score 1.0,
   `is_real_browser=true`).
3. Only after that gate passes: build `read_browser_console_v1`
   (forcing `browser_mode=playwright`), then run
   `python scripts/run_full_browser_gate.py`.

## Do not (still)

- Do not install Playwright/Chromium here, run the real gates, start
  `read_browser_console`, add a scheduled reaper, or modify stable skills /
  `safety_gate` / `promotion_policy`.
