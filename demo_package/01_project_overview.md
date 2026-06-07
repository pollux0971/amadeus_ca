# 01 — Project Overview

## What this is

A **browser-use / computer-agent / harness-engineering** project. The focus is not a
clever prompt — it is the **harness**: the external framework that controls context,
tools, traces, evaluation, safety, and promotion around a model. The system can
drive a real browser, patch + test code, and evolve its own skills — but only
through **gated, testable steps**.

## What this is NOT

- **Not an unbounded autonomous agent.** Every capability is a **gated phase** and
  every forward task is a **bounded story** (`docs/epics/`) — one story per run, no
  auto-extension.
- **Not calling a real LLM by default.** The provider layer is **fake-only** until a
  real-provider gate is cleared; the loader fails closed (`src/llm/`).
- **Not self-promoting.** The repair → apply → merge → staging chain stops at
  workspaces; **stable promotion is still blocked** behind human + policy + rollback
  + shell-execution review.
- **Not an action UI.** The dashboard is **read-only**: it visualizes a redacted
  snapshot and triggers nothing.

## Core ideas

- **Harness-first architecture** — control context/tools/trace/evaluation externally.
- **Skills as testable assets** — each skill has tests + evals, not just markdown.
- **CLI + Browser isolation (ADR-003)** — browser/page content is untrusted and can
  never become a shell command, tool call, repair, or promotion.
- **Trace-based evaluation** — every run saves trace + score + artifacts (redacted).
- **Gated self-evolution** — fake planner → execution bridge → repair proposal →
  approved apply → candidate merge → staging, each frozen by a checkpoint.

## Current high-level status

- Real-browser end-to-end is green (Phase 1B).
- The fake self-evolution chain is green through staging (Phases 2A–6).
- The Epic/Story backlog, a read-only UI dashboard, and a dashboard real-browser
  smoke gate are done.
- **Stable promotion: blocked.** No real API. stable / safety_gate / promotion_policy
  untouched.

See [`05_phase_timeline.md`](05_phase_timeline.md) for the full timeline and
[`06_safety_boundaries.md`](06_safety_boundaries.md) for the hard limits.
