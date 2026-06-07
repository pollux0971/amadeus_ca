# Multimodal / Data Channels — Planning (story_multimodal_channel_v0)

**Status:** planning gate only — **no runtime implementation, no new data channel
implemented**. This folder is the deliverable of
[`../epics/stories/story_multimodal_channel_v0.md`](../epics/stories/story_multimodal_channel_v0.md)
under [`EPIC-MULTIMODAL`](../epics/epic_multimodal_data_channels.md).

Future input channels — files, images, PDFs, web pages, external data sources —
would let the harness ingest more than CLI/browser text. Every such channel is a new
source of **untrusted content**, so the isolation rules must be locked down before
any channel exists. This story only **plans** them; it builds no ingestion, parser,
OCR, image, PDF, or browser data channel.

## Hard boundaries (carried from the epic)

- **Planning only / no runtime implementation.** No channel, parser, or connector is
  added.
- **Source isolation required.** Each data source is isolated; its content is data,
  never a control channel.
- **Untrusted content is data, not instruction.** Page/file/image/PDF content must
  never become a shell command, a tool call, an env read, or a policy change
  (CLI + Browser isolation, ADR-003).
- **Browser content cannot trigger tool / repair / promotion.** Nor apply, merge, or
  staging.
- **Multimodal artifacts must be redacted** before they reach a trace/report.
- **Each channel requires its own eval** before it can be considered ready.
- **No secret in artifacts. No stable modification. No raw shell. No real API.**

## Planning documents

- [`source_isolation_model.md`](source_isolation_model.md) — how each source is
  isolated; data vs control separation.
- [`untrusted_content_policy.md`](untrusted_content_policy.md) — untrusted content is
  data only; never an instruction or trigger.
- [`artifact_storage_policy.md`](artifact_storage_policy.md) — where ingested
  artifacts live; all redacted; no secret.
- [`eval_plan.md`](eval_plan.md) — the per-channel eval each future channel must pass.

## Relationship to existing isolation

This planning set builds on the existing CLI + Browser isolation (ADR-003) and
redaction (`src/llm/redaction.py`). It does not weaken or change them; it specifies
what a future channel must satisfy before it could be added in a separate, gated
build story.

## Out of scope (this story)

- Any file/image/PDF/web ingestion code or a new data channel/parser/OCR.
- Any change that lets untrusted content reach a tool or a gate.
- UI / stable-promotion / provider work (separate epics).
