# 08 — Teacher Presentation Outline (5–8 minutes)

A tight talk track for presenting the project. Times are guidance; total ≈ 5–8 min.

## 0:00–0:45 · Problem

- Autonomous browser/computer agents are powerful but dangerous: they can run shell
  commands, leak secrets, or change production behavior.
- The hard problem isn't the prompt — it's **control**: how do you let an agent do
  real work (drive a browser, patch code, evolve skills) **without** an unbounded
  blast radius?

## 0:45–1:30 · System goal

- A **harness-engineered** agent: capabilities are added as **gated, testable
  phases**; every forward task is a **bounded story**.
- Defaults are safe: **fake LLM provider**, **read-only dashboard**, **stable
  promotion blocked**.

## 1:30–2:45 · Harness engineering method

- Harness controls context / tools / **trace** / **evaluation** / **safety gate** /
  **promotion**.
- Skills are testable assets (tests + evals). CLI + Browser isolation: browser
  content is untrusted data, never an instruction.
- Show `python scripts/validate_workflows.py` (all gates green) — see
  [`03_demo_commands.md`](03_demo_commands.md).

## 2:45–3:45 · Browser e2e demo

- `python scripts/run_demo.py --demo vite_login_bug` → score 1.0 (sandboxed patch +
  tests).
- `python scripts/run_full_browser_gate.py --dry-run` (safe), and note the real
  Playwright e2e (Phase 1B) is 1.0 in the `.venv`.

## 3:45–5:00 · Fake planner / repair chain

- Walk the chain: fake planner → execution bridge → **repair proposal → approved
  apply → candidate merge → staging** — each **workspace-only**, human-gated, with
  rollback + a promotion review package (see [`05_phase_timeline.md`](05_phase_timeline.md)).
- Key point: the system can *propose and stage* its own fixes, but **cannot promote
  to stable** on its own.

## 5:00–6:00 · Dashboard demo

- `python scripts/generate_dashboard_snapshot.py` → `python scripts/validate_dashboard.py`
  → open `ui_dashboard/static/index.html`.
- `python scripts/run_dashboard_smoke.py --dry-run` (and note the real-browser smoke
  is 1.0). Emphasize: **read-only, no actions, no secrets, no external network**.

## 6:00–7:00 · Safety boundaries

- The hard "never" list ([`06_safety_boundaries.md`](06_safety_boundaries.md)): no
  real API, no `password_and_api.txt`, no stable/safety/promotion modification, no
  raw shell, no secret in artifacts, browser content can't trigger tools/repair/
  promotion, every long-run task is a bounded story.
- All enforced by validators + the secret hygiene scanner + per-story tests.

## 7:00–8:00 · Future work & close

- Decision matrix ([`07_next_steps.md`](07_next_steps.md)): Stable Promotion
  (blocked/high-risk), Real Provider (planning, operator opt-in), Multimodal
  (planning, per-channel isolation eval), action UI (new gates).
- Close: **the contribution is the safe, gated harness** — real capability with a
  bounded, auditable blast radius.
