# 05 · Demo Script

Run all commands from the repo root. None of these launch a real browser or
install anything. Each demo lists the command, the expected output, and how to
narrate it.

## Demo A — Walking skeleton

**Command**
```bash
python scripts/run_eval.py --task evals/walking_skeleton/inspect_only.yaml
```
**Expected**
```text
[PASS] inspect_only  score=1.0  run=runs/inspect_only_...
  [x] project_inspected
  [x] project_type_detected
```
**Narration:** "This proves the whole loop is wired: the harness reads an eval
task, loads the skill registry, runs a skill, writes a trace, and the evaluator
produces a score. It's not smart — but every core module is exercised."

## Demo B — patch_file_and_run_tests_v2 fixes vite_login_bug

**Command**
```bash
python scripts/run_demo.py --demo vite_login_bug
```
**Expected**
```text
[PASS] demo `vite_login_bug` score=1.0
  [x] dev_server_started
  [x] browser_opened_localhost
  [x] console_error_collected
  [x] source_file_patched
  [x] tests_pass
  [x] browser_has_no_fatal_console_error
```
**Narration:** "A real bug fix end-to-end: start a server (keep-alive), open it,
patch `App.jsx` via a declarative plan on a sandbox copy, run the tests. The patch
runner is reusable — no hard-coded fix."

## Demo C — py_calc_bug non-vite e2e

**Command**
```bash
python scripts/run_eval.py --task evals/patch_runner/py_calc_bug_e2e.yaml
```
**Expected**
```text
[PASS] py_calc_bug_e2e  score=1.0
  [x] source_file_patched
  [x] tests_pass
```
**Narration:** "The same patch runner fixes a *different*, non-vite fixture using a
`unified_diff` plan, with the eval supplying its own `test_command`. This proves
generality — it isn't hard-coded to App.jsx."

## Demo D — start_local_server keep_alive smoke

**Command**
```bash
python scripts/run_eval.py --task evals/server/keep_alive_smoke.yaml
```
**Expected**
```text
[PASS] keep_alive_smoke  score=1.0
  [x] dev_server_started
```
**Narration:** "The server starts and stays alive for a later step, then the
orchestrator tears it down at the end of the run — no lingering process. A lease
reaper backs this up if the orchestrator ever crashes."

## Demo E — open_localhost_browser HTTP fallback smoke

**Command**
```bash
python scripts/run_eval.py --task evals/browser/open_localhost_keep_alive_smoke.yaml
```
**Expected**
```text
[PASS] open_localhost_keep_alive_smoke  score=1.0
  [x] server_started
  [x] browser_page_loaded
  [x] page_snapshot_created
  [x] result_json_created
  [x] no_lingering_server_process
```
**Narration:** "The browser skill consumes the live server URL and loads the page.
Important honesty: in this environment there is no Playwright, so it uses an HTTP
fallback — `engine=http_fallback`, `is_real_browser=false`. **This is a localhost
smoke, not a real browser.** That's why the real-browser gate exists and why
`read_browser_console` is blocked."

## Safe gate dry-runs (show, don't run for real)

```bash
python scripts/run_playwright_gate.py --dry-run
python scripts/run_full_browser_gate.py --dry-run
```
**Narration:** "These gates are scaffolded but refuse to run until Playwright +
Chromium (and, for the full gate, a console candidate) exist. `--dry-run` just
lists the blocked prerequisites."
