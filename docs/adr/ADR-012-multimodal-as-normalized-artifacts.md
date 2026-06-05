# ADR-012: Multimodal Inputs as Normalized Artifacts

## Status

Accepted.

## Context

Images, PDFs, audio, video, and sensor streams can be large, private, and expensive to process. Injecting raw multimodal outputs into prompts would harm efficiency and reliability.

## Decision

Multimodal inputs are represented as normalized `ArtifactRef` records. Agents receive summaries, metadata, and evidence refs by default. Raw files remain accessible only through approved tools and safety policies.

## Consequences

- Context stays short.
- Raw material remains auditable and replayable.
- Modality-specific processing can be added incrementally.
- Critical identifiers and evidence references must be preserved during compression.
