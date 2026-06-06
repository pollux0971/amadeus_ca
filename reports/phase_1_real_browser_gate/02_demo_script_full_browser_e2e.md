# Demo Script — Full Real-Browser E2E

## Demo goal

Show that the harness drives a **real browser** end to end: start a local server,
open it in real Chromium, read the real console, patch the source and run its
tests, then **re-open the browser and re-read the console** to confirm no fatal
error remains — and that nothing leaks (server torn down). This proves a real
**browser + CLI + patch** loop, not a fabricated/HTTP-fallback one.

> Requires Playwright + Chromium (installed in the project `.venv`).

## Command

```bash
python scripts/run_full_browser_gate.py            # the gate (checks prereqs, then runs)
# or directly:
python scripts/run_eval.py --task evals/browser/full_browser_vite_login_bug_e2e.yaml
```

(`python scripts/run_full_browser_gate.py --dry-run` is safe anywhere — it only
lists prerequisites and runs nothing.)

## Expected output

```text
  [check] playwright_python_package: MET
  [check] chromium_runtime: MET
  [check] open_localhost_browser_v1_staging_ready: MET (status=staging-ready)
  [check] read_browser_console_candidate_exists: MET
[OK] all prerequisites met. Running the full real-browser e2e...
[PASS] full_browser_vite_login_bug_e2e  score=1.0
  [x] server_started
  [x] real_browser_page_loaded
  [x] console_error_collected
  [x] patch_applied
  [x] tests_pass
  [x] browser_reverify_passed
  [x] no_fatal_console_error_after_patch
  [x] no_lingering_server_process
```

## How to explain it

- **Pre-patch console.** The first browser open loads the live page in real
  Chromium and `read_browser_console` captures the *real* console — including the
  login bug's `console.error`. "We collected an actual browser console error,
  classified into error/warning/info/debug; uncaught exceptions would count as
  fatal."
- **Patch + tests.** `patch_file_and_run_tests_v2` applies a declarative
  `unified_diff` to a **sandbox copy** of the fixture's `login.py` and runs
  `python3 test_login.py` through the Safety Gate. "The source bug is fixed and
  verified by its test — `patch_applied` and `tests_pass`."
- **Post-patch reverify.** The browser is **re-opened** (a fresh real Chromium
  load) and the console re-read. "`browser_reverify_passed` = the page still loads
  in a real browser; `no_fatal_console_error_after_patch` = the post-patch console
  has **fatal = 0** (no uncaught error)."
- **No lingering process.** "The server was kept alive for the whole chain and the
  orchestrator tore it down in a `finally`; a precise process check shows nothing
  from the gate remains."
- **Why this matters.** "Every result is honestly tagged `engine=playwright`,
  `is_real_browser=true`. The same skills degrade to a non-browser smoke when
  Playwright is absent, but the gate requires the real engine — `http_fallback is
  not a real browser`. So this demonstrates a genuine browser + CLI + patch loop,
  measured and gated, not a demo trick."
