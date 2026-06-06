# EPIC-MULTIMODAL — Multimodal / Data Channels (planning only)

**Status:** planning only — no data channel implemented in this epic's v0 story.
**Depends on:** CLI + Browser isolation (ADR-003), redaction (`src/llm/redaction.py`),
the eval harness.

## Goal

Plan future input channels — files, images, PDFs, web pages, external data sources —
that the harness could consume. **This epic's current scope is planning only**; no
new channel is implemented.

## Why isolation / planning first

Every new input channel is a new source of **untrusted content**. Without strict
isolation, page/file content could become instructions, or trigger a tool,
promotion, or repair. The isolation and untrusted-content policy must be written
before any channel exists, and each channel needs its own eval.

## Hard rules (must be written into every story under this epic)

- **Source isolation.** Each data source is isolated; its content is data, never a
  control channel.
- **Untrusted content is never an instruction.** Page/file/image/PDF content must
  never be turned into a shell command, a tool call, an env read, or a policy
  change (CLI + Browser isolation, ADR-003).
- **Browser/untrusted content can never trigger a tool, promotion, repair, apply,
  merge, or staging.**
- **Multimodal artifacts must be redacted** before they reach a trace/report.
- **Each channel needs its own eval** before it can be considered ready.
- **No real API**, **no secret**, **no stable modification**, **no raw shell**.

## Stories

- [`stories/story_multimodal_channel_v0.md`](stories/story_multimodal_channel_v0.md)
  — multimodal/data channel **planning gate only**: source isolation model,
  untrusted-content policy, artifact storage policy, eval plan. No new channel
  implemented.

## Out of scope (for this epic, until a later gated story)

- Any actual file/image/PDF/web ingestion code or new data channel.
- Any change that lets untrusted content reach a tool or a gate.
- UI / stable-promotion / provider work (separate epics).
