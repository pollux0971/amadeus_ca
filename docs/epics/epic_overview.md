# Epic Overview

The backlog's top-level epics. Each epic is **planning-gated**: the v0 story under
each is a *planning / packaging* story only — no runtime feature work — and any
real implementation is a later, separately-gated story.

> **One bounded story at a time.** Pick the next story from
> [`decision_matrix.md`](decision_matrix.md); a `/goal` run executes exactly one
> bounded story and must not auto-extend into another.

## Status table

| Epic ID | Epic name | Status | Depends on | Current phase relation | Next allowed story | Forbidden shortcuts |
|---|---|---|---|---|---|---|
| EPIC-STABLE | Stable Promotion | planning / blocked | Phase 6 staging promotion (`checkpoint-phase-6-staging-promotion`) | Continues the repair→apply→merge→staging chain into stable | [`stories/story_stable_promotion_v0.md`](stories/story_stable_promotion_v0.md) | no auto stable write; no skipping promotion policy / rollback verification / human shell-execution review; no browser-triggered promotion |
| EPIC-UI | UI Dashboard (planning only) | planning | read-only over existing runs/reports/checkpoints | New read-only surface over the harness | [`stories/story_ui_dashboard_v0.md`](stories/story_ui_dashboard_v0.md) | no UI raw shell; no secret display; no promote-from-UI; no write actions outside existing approval-gated scripts |
| EPIC-PROVIDER | Real LLM Provider (planning only) | planning | `src/llm/` fake provider + config contract | Would replace the fake provider behind an opt-in | [`stories/story_real_provider_v0.md`](stories/story_real_provider_v0.md) | no real API call; no key in config; no reading password_and_api.txt; no provider client implemented in v0 |
| EPIC-MULTIMODAL | Multimodal / Data Channels (planning only) | planning | CLI+Browser isolation (ADR-003), redaction | New untrusted input surfaces | [`stories/story_multimodal_channel_v0.md`](stories/story_multimodal_channel_v0.md) | untrusted content as instruction; browser/file content triggering tool/promotion/repair; channel without its own eval |

## Status legend

- **planning** — only a planning/packaging story is allowed next; no runtime feature.
- **blocked** — preconditions (a human gate, a prior phase) are not met; the v0
  story may still produce the *package* a human needs, but must not act.
- **in progress** — a single bounded story is currently being executed.
- **done** — the story's Definition of Done is met and a checkpoint/report froze it.

## Global forbidden shortcuts (every epic)

- No real API call; fake provider is the default and the loader fails closed.
- No stable modification; no skipping the promotion policy.
- No raw shell / direct command outside fixed, vetted allowlists.
- No secret in any artifact; never read `.env` values or
  `/data/python/computer_agent_v5/password_and_api.txt`.
- Untrusted (browser/file/page) content can never trigger a tool, promotion,
  repair, apply, merge, or staging.
