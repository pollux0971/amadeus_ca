# 09 — Limitations

Honest limitations of the current system. None are hidden; several are deliberate
safety choices.

## Capability limitations

- **Fake provider only.** No real LLM reasoning is exercised; the provider is offline
  and deterministic. Real providers are planning-gated and require operator opt-in.
- **Deterministic fake planner / repair.** Plans and repair proposals are selected by
  **marker**, not semantic reasoning. The chain proves the *gating and safety*, not
  real model-generated fixes.
- **Self-evolution stops at staging.** The repair → apply → merge → staging chain is
  workspace-only; **stable promotion is blocked** (by design) and needs human gates.
- **Real-browser results need `.venv`.** Real-browser and dashboard-smoke 1.0 require
  Playwright/Chromium; under the system interpreter those steps degrade (e.g.
  planner-exec 0.9091). **http_fallback is not a real browser.**

## Scope limitations

- **Read-only dashboard.** It visualizes status only; it has no action surface. An
  action UI is future work behind new gates.
- **Single fixture domain.** The browser e2e centers on the `vite_login_bug` fixture;
  broader coverage is future work.
- **Rollback is workspace-level.** Current rollback = delete the workspace. A
  deployed-state rollback for a real stable cut is not yet defined/verified.

## Process limitations

- **Human gates are manual and unmet.** Stable promotion needs human shell-execution
  review, policy review, operator approval, and rollback verification — none captured.
- **Bounded-story cadence.** Progress is one bounded story per run by design; this is
  a safety feature, but it means no large autonomous sweeps.

## What these limitations are NOT

They are not silent gaps: each is recorded here, in the stable-promotion audit
(`reports/stable_promotion_readiness_audit_v0/`), and in the per-phase reports, and is
enforced by validators/tests rather than relying on prose.
