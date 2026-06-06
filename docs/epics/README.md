# Project Backlog — Epics & Stories

This is the project's formal backlog. It turns the completed phases / checkpoints /
reports into bounded **Epics** and **Stories** so future work (especially each
`/goal` run with Claude Code) stays inside one well-defined boundary and never
expands without an explicit decision.

## How to use this backlog

1. Read [`epic_overview.md`](epic_overview.md) for the Epic status table.
2. Read [`decision_matrix.md`](decision_matrix.md) to choose **one** next story
   (value vs risk vs dependencies vs required gates).
3. Open that story under [`stories/`](stories/) and work **only** within its
   `Scope`, `Acceptance Criteria`, and `Forbidden Zone`.
4. When the story's `Definition of Done` is met, **stop** — write a checkpoint or
   update a report. Do **not** auto-continue into the next story.

## One bounded story at a time

- **Each `/goal` run executes exactly ONE bounded story.** No cross-story
  auto-extension; no "while I'm here" scope creep.
- A story that turns out to be larger than its boundary must be **split** into a
  new story, not silently expanded.
- If preconditions are not met, the story is **blocked** — record that and stop.

## Relationship to phases / checkpoints

The phases already shipped are *history*, frozen by their checkpoints; the epics
are the *future*, gated the same way:

| Shipped phase (frozen checkpoint) | Backlog continuation |
|---|---|
| Phase 1B real-browser e2e | — (baseline) |
| Phase 2A fake planner execution bridge | — |
| Phase 3 repair proposal-only | — |
| Phase 4 approved patch application (workspace-only) | — |
| Phase 5 candidate merge (workspace-only) | — |
| Phase 6 staging promotion (workspace-only) | **EPIC-STABLE** (stable promotion) |
| (future surface) | **EPIC-UI**, **EPIC-PROVIDER**, **EPIC-MULTIMODAL** |

A completed story must end with a checkpoint (`docs/checkpoints/`) or a report
update (`reports/`), exactly like the phases — the checkpoint freezes the new
state and the next story starts from there.

## Hard boundaries (apply to every story)

- **stable / safety / promotion:** no automated phase modifies a stable skill, an
  active candidate runtime, `src/agents/safety_gate/`, or
  `specs/harness/promotion_policy.md`. **No stable modification.** Stable promotion
  is human-driven and policy-gated.
- **secret:** **no secret** in any artifact, trace, report, or commit; never read
  `.env` key values or `/data/python/computer_agent_v5/password_and_api.txt`; all
  artifacts redacted (`src/llm/redaction.py`).
- **shell:** **no raw shell** / direct command driven by a plan, proposal, merge,
  staging, UI, or browser content; only fixed, vetted allowlists.
- **provider:** **no real API** call by default; fake provider is the default;
  real providers are operator-opt-in and fail-closed (see EPIC-PROVIDER).
- **untrusted input:** browser/page/file content is untrusted and can never
  trigger a tool, promotion, repair, apply, merge, or staging.

## Files

- [`epic_overview.md`](epic_overview.md) — Epic status table.
- [`decision_matrix.md`](decision_matrix.md) — choose the next story.
- [`story_template.md`](story_template.md) — template for new stories.
- Epics: [`epic_stable_promotion.md`](epic_stable_promotion.md),
  [`epic_ui_dashboard.md`](epic_ui_dashboard.md),
  [`epic_real_provider.md`](epic_real_provider.md),
  [`epic_multimodal_data_channels.md`](epic_multimodal_data_channels.md).
- Stories: [`stories/`](stories/).
