# Story MULTIMODAL-V0 — Multimodal / data channel planning gate only

**Epic:** EPIC-MULTIMODAL
**Status:** done (planning gate only) — see
[`../../../reports/story_multimodal_channel_v0/README.md`](../../../reports/story_multimodal_channel_v0/README.md)
and [`../../multimodal_data_channels/`](../../multimodal_data_channels/).

## Goal

Plan future input channels (files, images, PDFs, web pages, external data) under
strict isolation — **planning only**, no new channel implemented.

## Scope

- Write the **source isolation model** (each source isolated; content is data, not
  control).
- Write the **untrusted-content policy** (untrusted content is never an instruction
  and never triggers a tool/promotion/repair/apply/merge/staging).
- Write the **artifact storage policy** (where ingested artifacts live; all
  redacted).
- Write the **eval plan** (each channel gets its own eval before it is ready).

## Out of Scope

- Any actual file/image/PDF/web ingestion code or a new data channel.
- Any change that lets untrusted content reach a tool or a gate.

## Preconditions

- CLI + Browser isolation (ADR-003) and redaction (`src/llm/redaction.py`) exist.

## Implementation Boundaries

- May write only planning docs (under `docs/` and/or `specs/`).
- May **not** add any ingestion channel, parser, or data-source connector.

## Acceptance Criteria

- [ ] source isolation model written
- [ ] untrusted content policy written (content never becomes an instruction)
- [ ] artifact storage policy written (redacted artifacts only)
- [ ] eval plan written (per-channel eval required before ready)
- [ ] no new channel implemented

## Forbidden Zone

- **Untrusted content as instruction** is forbidden.
- **Browser/file/page content can never trigger a tool, promotion, repair, apply,
  merge, or staging.**
- Multimodal artifacts must be redacted. No real API. No stable modification. No
  raw shell. No secret.

## Required Validation Commands

```bash
python scripts/validate_structure.py
python scripts/validate_workflows.py
python scripts/check_secret_hygiene.py
python scripts/run_unit_tests.py
```

## Artifacts to Produce

- Planning docs: source isolation model, untrusted-content policy, artifact storage
  policy, per-channel eval plan (all redacted; no secret).

## Rollback / Stop Condition

- **Rollback:** delete the planning docs — nothing runtime changed; no channel added.
- **Stop Condition:** stop when the Definition of Done is met; do not implement any
  channel or continue into another story.

## Definition of Done

Acceptance criteria met; validation green; planning docs exist; no channel
implemented; working tree clean; **stop**.
