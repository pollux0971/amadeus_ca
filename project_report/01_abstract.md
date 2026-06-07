# 01 — Abstract

This is a **browser-use / computer-agent / harness-engineering** project. Its
contribution is not a single clever agent but a **gated harness**: an external
framework that lets an AI agent manage a real browser, a CLI, a planner, and a
self-repair loop **without** becoming an unbounded autonomous agent.

The core goal: every capability is added as a **gated, testable phase**, and every
forward task is a **bounded story** (one per run, no auto-extension). Defaults are
safe — a **fake LLM provider** (no real API), a **read-only dashboard**, and a
**blocked stable promotion**.

The system is green end-to-end on a real browser (Phase 1B) and runs a complete,
human-gated self-evolution chain through staging (Phases 2A–6): fake planner →
execution bridge → repair proposal → approved apply → candidate merge → staging
promotion, each stopping at a workspace. A formal **Stable Promotion Readiness
Audit** concludes **NO-GO / BLOCKED** because the required human gates are unmet.
Throughout, stable skills, the safety gate, and the promotion policy are untouched;
no secret is committed; no real API is called.

Headline numbers (this report): unit tests **453/453**; `vite_login_bug` demo
**1.0**; real-browser e2e **1.0** (`.venv`); dashboard read-only smoke **1.0**
(`.venv`); repair/planner evals **1.0**.
