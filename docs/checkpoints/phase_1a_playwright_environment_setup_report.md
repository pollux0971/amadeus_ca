# Phase 1A — Playwright Environment Setup & Real-Browser Gate Report

Outcome of installing Playwright + Chromium in an isolated project venv and
running `scripts/run_playwright_gate.py`. **The gate PASSED (score 1.0,
is_real_browser=true).** Branch B was **NOT** applied — that awaits operator
confirmation.

## Environment

- **timestamp:** 2026-06-05T22:38:24Z
- **python version:** 3.12.3 (`python` not present; `python3` = `/usr/bin/python3`)
- **pip environment:** system Python is externally-managed (PEP 668). Per operator
  approval, an **isolated project venv** was created at `.venv` (gitignored).
  - venv: `.venv/bin/python` (Python 3.12.3, pip 24.0), `in_venv: True`.
  - **No sudo. No global install. No `install-deps`/apt.**
- **playwright package version:** **1.60.0** (installed into `.venv`).
- **declared deps completed in venv:** `pyyaml 6.0.3` (project `dev` extra;
  needed so `simple_yaml` uses PyYAML instead of the fallback parser — see Notes).
- **chromium install status:** **OK** — `python -m playwright install chromium`
  downloaded Chromium + headless shell + ffmpeg to
  `/home/pollux/.cache/ms-playwright/` (not in the repo; gitignored cache).
  Executable present: `/home/pollux/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome`.
  Headless launch + JS probe succeeded.

## Gate run

- **dry-run (via venv):** `playwright python package: FOUND` (exit 0).
- **real gate command:** `.venv/bin/python scripts/run_playwright_gate.py`
- **real gate exit code:** **0 (PASS)**
- `run_full_browser_gate.py` was **NOT** run (read_browser_console does not exist).

### Gate result (eval `open_localhost_playwright_required_smoke`)

- **score:** **1.0**
- **engine:** `playwright`
- **is_real_browser:** `true`
- **screenshot_supported:** `true`
- **js_supported:** `true`
- **console_supported:** `true`
- score metrics: `browser_engine=playwright`, `browser_is_real=true`
- **criteria (all 10 pass):** server_started, browser_page_loaded,
  engine_is_playwright, is_real_browser, screenshot_supported, js_supported,
  console_supported, page_snapshot_created, screenshot_created,
  no_lingering_server_process.

### Artifacts (this gate run)

- run dir: `runs/open_localhost_playwright_required_smoke_1780699000_203f73b3/`
  (`score.json`, `trace.jsonl`, `summary.md`, `task.yaml`).
- browser artifacts (temp dir `/tmp/browser_artifacts_1t5sdx0l/`, ephemeral — not
  committed):
  - `result.json` — `status=loaded`, `engine=playwright`, `is_real_browser=true`,
    `status_code=200`, `title="Keep-Alive Demo"`.
  - `page_snapshot.json` — `url=http://127.0.0.1:43049`, `title="Keep-Alive Demo"`,
    counts `{links:1, buttons:2, forms:1}`.
  - `screenshot.png` — **real rendered PNG, 1280×720, 13127 bytes** (not committed;
    regenerate by re-running the gate).

### No lingering process

- Precise check for gate-spawned processes
  (`ms-playwright|headless_shell|chrome-linux64/chrome|node server.js|http.server`):
  **NONE** ✅. The orchestrator tore down the kept-alive server; the candidate
  closed its Playwright browser/context.
- Note: ~43 `/opt/google/chrome/chrome` processes exist on the host — these are the
  **operator's pre-existing desktop Chrome** (`~/.config/google-chrome`), unrelated
  to and untouched by the gate.

## Repo invariants (re-verified, system interpreter)

- `validate_structure` / `validate_workflows` PASS; `run_skill_tests` 5/5;
  `run_unit_tests` 113/113.
- `open_localhost_keep_alive_smoke` 1.0, `py_calc_bug_e2e` 1.0,
  `vite_login_bug` 1.0 (unchanged http_fallback baseline under system python).
- `open_localhost_browser_v1` status: **dev** (UNCHANGED — not promoted).
- `read_browser_console`: no candidate (still **blocked**).
- stable skills / safety_gate / promotion_policy **untouched**. No runtime code
  changed.

## Whether Branch B can be applied

**Yes — the gate's pass satisfies the Branch B trigger condition.** But Branch B
was deliberately **NOT** applied this round (per task: only report; wait for
operator confirmation). The pre-apply checklist is
`docs/branch_b_playwright_gate_passed_draft/branch_b_apply_checklist.md`.

## Next recommended step

1. Operator reviews this report + the gate evidence and **approves** applying
   Branch B.
2. Apply the Branch B drafts (matrix/promotion/milestone/quick_resume +
   `open_localhost_browser_v1` `status: dev → staging-ready`) and create
   `phase_1a_playwright_gate_passed.md`.
3. Then start `read_browser_console_v1` (must force `browser_mode=playwright`).

## Notes / items that may need operator decision

- **PyYAML in venv:** the gate initially crashed (`int('1.2')`) because the fresh
  venv lacked PyYAML, so `simple_yaml` fell back to its subset parser (which keeps
  `version: 1.2` as a string). Installing the **already-declared** `pyyaml` dep
  fixed it (matches the system baseline). No code changed. If you want CI to use a
  venv, `pyyaml` + `playwright` should be installed from the `dev` + `browser`
  extras; say the word if you want a `requirements.txt`/lockfile added to the repo.
- **No system dependencies were missing** — headless Chromium launched without
  `install-deps`/sudo on this host.
