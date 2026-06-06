# EPIC-UI — UI Dashboard (planning only)

**Status:** planning only — no UI implementation in this epic's v0 story.
**Depends on:** read-only access to existing `runs/`, `reports/`, `docs/checkpoints/`,
`evals/`, candidate status docs.

## Goal

Plan a future read-only dashboard that surfaces the harness state — phases, gates,
evals, candidates, runs, reports — so a human can see status at a glance. **This
epic's current scope is planning only**; no UI is built yet.

## Why read-only / planning first

A dashboard is an outward-facing surface. If it could trigger actions or render raw
artifacts it would become a new attack surface and a new way to leak secrets or
bypass gates. So the design must be locked down before any code exists.

## Hard rules (must be written into every story under this epic)

- **UI must not trigger raw shell** or any direct command.
- **UI must not display secret** — it renders only redacted artifacts
  (`src/llm/redaction.py`); raw `runs/` content is never shown unredacted.
- **UI must not directly promote** anything — no promote/apply/merge/stage button
  that bypasses the existing gates.
- **UI is read-only over redacted artifacts.** Any action it offers must route
  through an **existing approval-gated script** (e.g. `repair_*`, `staging_promote`)
  with the same human-approval markers — never a new privileged path.
- **No real API**, **no secret**, **no stable modification**, **no raw shell**.

## Stories

- [`stories/story_ui_dashboard_v0.md`](stories/story_ui_dashboard_v0.md) — UI
  dashboard **planning only**: information architecture, redacted-artifact model,
  and a future eval list. No action execution, no rendering of secrets.

## Out of scope (for this epic, until a later gated story)

- Any actual web/app code beyond what already exists under `apps/` as placeholders.
- Any write action, promotion, or live control surface.
- Provider / stable-promotion / multimodal work (separate epics).
