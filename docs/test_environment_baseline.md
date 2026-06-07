# Test Environment Baseline

This document **locks down the difference between the two Python interpreters** used
to run this project's tests, so that an *environment gap* is never mistaken for a
*regression*. It is the authoritative reference for "which interpreter must I use,
and is this failure real?"

> **One-line rule.** A test that fails **only because of the interpreter / browser
> runtime** is an *environment gap*, not a regression. A test that fails **because of
> a code change** is a regression and must be fixed. Never let a known failing
> baseline hide a new failure — see [Regression vs environment gap](#regression-vs-environment-gap).

Reproduce the current baseline with:

```bash
.venv/bin/python scripts/check_test_environment_baseline.py
```

---

## The two interpreters

| | **System Python** | **Project `.venv`** |
|---|---|---|
| Path | `/usr/bin/python3` (often **not** on `PATH` as bare `python`) | `.venv/bin/python` |
| Playwright package | **absent** | **installed** |
| Chromium runtime | **absent** | **installed** |
| Browser engine used by evals | `http_fallback` (degraded; **not a real browser**) | `playwright` (**real browser**) |
| Real-browser gates / evals | **cannot** run (blocked / degraded) | **run for real** (this is the real-browser verification path) |

- **`python` is frequently not on `PATH`** in this environment. Use an explicit
  interpreter (`.venv/bin/python` or `/usr/bin/python3`). The baseline checker treats
  a missing bare `python` as a **WARNING only — never a failure**.
- **`.venv/bin/python` is the real-browser verification path.** Any gate or eval that
  must prove a *real* browser (`engine=playwright`, `is_real_browser=true`) MUST be
  run with `.venv/bin/python`. `http_fallback` is **not** a real browser.

---

## What runs where

### Must run on `.venv/bin/python` (real browser / Playwright required)

These need the Playwright package + a Chromium runtime to verify a *real* browser.
On system Python they are blocked or degrade to `http_fallback`:

- `scripts/run_playwright_gate.py` (non-dry-run)
- `scripts/run_full_browser_gate.py` (non-dry-run) — `full_browser_vite_login_bug_e2e`
  + `fake_full_browser_plan_execution`
- `scripts/run_dashboard_smoke.py` (non-dry-run) — `ui_dashboard_readonly_smoke`
- `evals/browser/*` and `evals/planner/fake_full_browser_plan_execution.yaml` that
  assert `browser_mode: playwright` / `require_real_browser: true`

### Safe on either interpreter (dry-run / no browser / no install)

These never launch a browser and never install anything, so they behave the same on
system Python and `.venv` (prefer `.venv/bin/python` for one consistent path):

- `scripts/validate_structure.py`
- `scripts/validate_workflows.py`
- `scripts/check_secret_hygiene.py`
- `scripts/validate_config.py`
- `scripts/check_test_environment_baseline.py`
- `scripts/llm_smoke.py --fake-only`
- `scripts/run_playwright_gate.py --dry-run`
- `scripts/run_full_browser_gate.py --dry-run`
- `scripts/run_dashboard_smoke.py --dry-run`
- `scripts/run_demo.py --demo vite_login_bug` (uses `http_fallback`; real-browser proof is the `.venv` gate)
- `scripts/run_skill_tests.py`

---

## Unit-test baseline (`scripts/run_unit_tests.py`)

The full unit suite has **interpreter-coupled** results. This is expected and locked
here:

| Interpreter | Result | Notes |
|---|---|---|
| **System `/usr/bin/python3`** | **519/519 pass, 0 failed** | Playwright absent → browser evals use `http_fallback`, which is exactly what the env-gap tests below assume. |
| **`.venv/bin/python`** | **517/519 pass, 2 failed** | Playwright present → the 2 tests below assume a *Playwright-absent* environment and therefore fail. |

### Known environment-gap tests (NOT regressions)

These tests encode a **Playwright-absent assumption**. They **pass on system Python**
and **fail on `.venv`** because, with the real browser present, the harness reports
the real engine instead of the degraded `http_fallback` the test expects, or the gate
no longer "blocks on missing prerequisites":

1. `tests/unit/test_browser_keep_alive_e2e.py::test_browser_keep_alive_smoke_scores_1_and_no_lingering`
   — asserts `browser_engine == "http_fallback"` and `browser_is_real is False`.
   On `.venv` the real Playwright engine is used, so these two assertions fail. The
   **real-browser** equivalent is verified positively by the `.venv` real-browser gate
   (`engine=playwright`, `is_real_browser=true`, score 1.0).
2. `tests/unit/test_full_browser_gate_script.py::test_missing_prereqs_block_with_exit_2`
   — asserts the gate **blocks with exit 2** because "Playwright is absent". On `.venv`
   the prerequisites are met, so the gate does **not** block — the assertion fails.
   The positive path (the gate actually running and scoring 1.0) is the `.venv`
   real-browser verification.

> These 2 are the **entire** known-env-gap set as of this baseline. They must **not**
> be "fixed" by weakening them, and they must **not** be used to excuse any *other*
> failure. If the failing set on `.venv` is anything other than exactly these two,
> investigate it as a possible regression.

---

## Regression vs environment gap

Use this decision rule whenever a test fails:

1. **Is the failing test in the [known environment-gap set](#known-environment-gap-tests-not-regressions) above?**
   - If **yes** and you are on `.venv`, it is an **environment gap** — expected,
     not a regression. The same test **passes on system Python**.
   - Confirm by running it on `/usr/bin/python3`; it should pass there.
2. **Did your change touch `src/` runtime, a skill, an eval, or a script under test?**
   - If the failing test is *not* in the env-gap set, treat it as a **regression**
     until proven otherwise — bisect against the clean baseline (e.g. `git stash` your
     change and re-run the same test under the **same** interpreter).
3. **Cross-interpreter check.** A genuine regression typically fails under **both**
   interpreters, or newly fails a test that previously passed under the interpreter
   you are using. An environment gap fails under **only one** interpreter and matches
   the known set.
4. **Never mask a new failure with the baseline.** "517/519, same 2 as before" is
   only acceptable if the failing names are **exactly** the two known env-gap tests.
   If a third name appears, or a different name replaces one of them, that is a
   regression to investigate — do **not** wave it through as "pre-existing".

### Quick commands

```bash
# Baseline summary (no browser, no install, no network):
.venv/bin/python scripts/check_test_environment_baseline.py

# Confirm a .venv failure is an environment gap (should pass on system Python):
/usr/bin/python3 scripts/run_unit_tests.py        # expect 519/519

# Real-browser verification path (only on .venv):
.venv/bin/python scripts/run_full_browser_gate.py        # real browser; expect 1.0
.venv/bin/python scripts/run_dashboard_smoke.py          # real browser; expect 1.0
```

---

## For future stories

- **Every story must state its execution path** — whether each command runs on
  `system` Python or the `.venv` (see `docs/next_milestone_plan.md`).
- **Real-browser claims require `.venv/bin/python`.** Do not claim a real-browser
  result from an `http_fallback` run.
- **Re-run the baseline checker** (`scripts/check_test_environment_baseline.py`) when
  the environment changes (new interpreter, Playwright (un)installed) and update the
  [known env-gap set](#known-environment-gap-tests-not-regressions) here if — and only
  if — the *environment*, not the code, changed it.
- This baseline does **no** real API call, installs **nothing**, downloads **no**
  browser, reads **no** secret, and modifies **no** runtime / stable skill /
  `safety_gate` / `promotion_policy`.
