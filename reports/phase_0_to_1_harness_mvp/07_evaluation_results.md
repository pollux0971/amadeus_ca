# 07 · Evaluation Results

Snapshot at checkpoint `checkpoint-0-to-1-harness-gates`. All commands are run
from the repo root; none launch a real browser or install anything.

## Test + validation status

| Check | Result |
|---|---|
| `python scripts/validate_structure.py` | PASS |
| `python scripts/validate_workflows.py` | PASS (incl. candidate/phase docs checks) |
| `python scripts/run_skill_tests.py` | 5/5 PASS |
| `python scripts/run_unit_tests.py` | **98/98 PASS** |

## Eval / demo scores

| Eval / demo | Score | Notes |
|---|---|---|
| `vite_login_bug` (demo) | **1.0** | real server keep_alive + browser load + real patch |
| `py_calc_bug_e2e` | **1.0** | non-vite, `unified_diff` plan, eval-supplied test_command |
| `keep_alive_smoke` (server) | **1.0** | server kept alive then torn down by the orchestrator |
| `open_localhost_keep_alive_smoke` (browser) | **1.0** | `browser_engine=http_fallback`, `browser_is_real=false` |

## Gates

| Gate | Status |
|---|---|
| Playwright real-browser gate | **NOT executed** — no Playwright/Chromium here; `--dry-run` safe |
| Full browser e2e gate | **draft / blocked** — runner exits 2 until prereqs exist; `--dry-run` safe |

## Process / safety invariants

- **No lingering server/browser processes** after any run; the `_sessions`
  registry is empty after a clean run.
- **stable skills / safety_gate / promotion_policy untouched** throughout the
  phase.
- The browser smoke score is honestly labeled: a passing 1.0 carries
  `engine=http_fallback`, `is_real_browser=false` — it is **not** a real browser
  result.

## Active overrides at this checkpoint

```text
open_localhost_browser     -> open_localhost_browser_v1
patch_file_and_run_tests   -> patch_file_and_run_tests_v2
start_local_server         -> start_local_server_v1   (release 1.2)
```
