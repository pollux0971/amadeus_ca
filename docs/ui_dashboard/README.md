# UI Dashboard — Planning (story_ui_dashboard_v0)

**Status:** planning only — **no UI implemented**. This folder is the deliverable of
[`../epics/stories/story_ui_dashboard_v0.md`](../epics/stories/story_ui_dashboard_v0.md)
under [`EPIC-UI`](../epics/epic_ui_dashboard.md).

A future dashboard would surface the harness state (phases, gates, evals,
candidates, runs, reports) so a human can see status at a glance. This story only
**plans** it; it builds no UI and executes no action.

## Hard boundaries (carried from the epic)

- **No action execution.** The design is **read-only**; no button runs anything.
- **No raw shell.** The UI never triggers a raw shell or direct command.
- **No secret display.** Only redacted artifacts are shown (`src/llm/redaction.py`);
  raw `runs/` content is never rendered unredacted.
- **No promotion from UI.** No promote / apply / merge / stage from the UI; any
  action must route through an **existing approval-gated script** with its
  human-approval markers — never a new privileged path.
- **Read-only over redacted artifacts.** The dashboard reads only what is already
  on disk (runs/reports/checkpoints/evals/candidate docs), redacted.

## Planning documents

- [`information_architecture.md`](information_architecture.md) — views/panels and
  the on-disk artifacts each reads.
- [`redacted_artifact_model.md`](redacted_artifact_model.md) — how artifacts are
  exposed read-only and redacted; what is never shown.
- [`future_eval_list.md`](future_eval_list.md) — evals to add **when** the UI is
  eventually built (none implemented now).

## Relationship to the existing placeholder

There is already a placeholder skeleton under
[`../../apps/web_console/`](../../apps/web_console/) (`README.md`,
`API_CONTRACT.md`). This planning set refines its **read-only, redacted, no-direct-
mutation** boundary; it does **not** add executable UI code. Any future build is a
separate, gated story.

## Out of scope (this story)

- Any web/app code beyond the existing `apps/` placeholders.
- Any write action, promotion, or live control surface.
- Provider / stable-promotion / multimodal work (separate epics).
