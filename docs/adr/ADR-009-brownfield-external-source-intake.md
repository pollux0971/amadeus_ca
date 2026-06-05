# ADR-009: Brownfield External Source Intake

## Status

Accepted.

## Context

Future work may add UI projects, open-source repositories, datasets, PDFs, screenshots, audio files, or multimodal samples. Directly copying these materials into stable runtime directories would make the harness hard to audit and unsafe for agent use.

## Decision

All new external materials must enter through `external/inbox/raw` with a manifest in `external/inbox/manifests`. They are then moved through staging, tests, and approval before runtime use.

## Consequences

- New features can be added without destabilizing the core harness.
- Agents can inspect approved artifacts without arbitrary filesystem access.
- Open-source projects can be studied before being integrated.
- The cost is extra setup: each source needs a manifest and intake step.
