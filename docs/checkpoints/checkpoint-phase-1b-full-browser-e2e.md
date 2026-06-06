# Checkpoint: Phase 1B — Full Real-Browser E2E

- **checkpoint name:** `checkpoint-phase-1b-full-browser-e2e`
- **commit (full e2e passed):** `b7fa1d5`
- **tag:** `checkpoint-phase-1b-full-browser-e2e`

Frozen snapshot of the complete real-browser chain. The full end-to-end gate is
wired and passing; this checkpoint freezes that state. Documentation only — no
runtime, candidate, stable skill, safety gate, or promotion policy change.

## Gate result (full_browser_vite_login_bug_e2e)

- **score = 1.0** (all 8 criteria) via `scripts/run_full_browser_gate.py` (exit 0)
  in a Playwright + Chromium environment.
- **engine=playwright**
- **is_real_browser=true**
- **pre-patch console counts** (`console_pre`):
  `{error: 1, warning: 1, info: 0, debug: 1, fatal: 0, total: 3}`
- **post-patch console counts** (`console_post`):
  `{error: 1, warning: 1, info: 0, debug: 1, fatal: 0, total: 3}`
- **patch_applied = true**
- **tests_pass = true**
- **browser_reverify_passed = true** (post-patch real-browser re-open)
- **no_fatal_console_error_after_patch = true** (post-patch fatal = 0)
- **no_lingering_server_browser_process = true**

## Chain

```
start_local_server (keep_alive)
  → open_localhost_browser  (open_pre,  real browser)
  → read_browser_console    (console_pre)
  → patch_file_and_run_tests
  → open_localhost_browser  (open_post, real browser RE-OPEN)
  → read_browser_console    (console_post)
  → orchestrator finally: teardown the kept-alive server
```

## Active overrides

```text
open_localhost_browser     -> open_localhost_browser_v1
patch_file_and_run_tests   -> patch_file_and_run_tests_v2
read_browser_console       -> read_browser_console_v1
start_local_server         -> start_local_server_v1   (release 1.2)
```

## Candidate stages

| Candidate | Stage |
|---|---|
| `patch_file_and_run_tests_v2` | staging-ready (after human shell review) |
| `start_local_server_v1.2` | dev / staging-candidate |
| `open_localhost_browser_v1` | staging-ready (Playwright gate passed) |
| `read_browser_console_v1` | dev (console smoke 1.0; real browser only) |
| `full_browser_vite_login_bug_e2e` | **passed** (executable gate) |

## Remaining risks

- **Stable promotion still needs review.** Shell-executing candidates
  (patch runner, start_local_server) need a human shell-execution review before
  `stable`. Passing the integration gate is **not** a stable promotion.
- **Real-browser runs require Playwright/Chromium** (installed in the project
  `.venv`); under interpreters without it the browser/console steps fail
  gracefully. **http_fallback is not a real browser.**
- `start_local_server` lease is advisory (not an OS-level watchdog).
- No LLM planner; no auto-repair loop; no UI/multimodal yet.

## Next possible phases (decision point — none started)

a. **LLM planner** — replace rule-based step selection.
b. **Claude / Codex auto-repair loop** — failure_report → candidate → eval → promotion.
c. **UI dashboard** — the `apps/` surface.
d. **Multimodal / data-channel extensions** — via brownfield intake → adapter → eval.

## Frozen constraints

- **stable skills / safety_gate / promotion_policy untouched** throughout.
- All real implementations live as candidates under `harnesses/candidates/`.
- No `.venv` / browser cache / runs / screenshots / secrets are committed.
