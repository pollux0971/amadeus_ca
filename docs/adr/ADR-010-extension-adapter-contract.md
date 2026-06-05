# ADR-010: Extension Adapter Contract

## Status

Accepted.

## Context

The harness will eventually support new interfaces, channels, tools, and modalities. If each extension modifies the orchestrator directly, the system will become brittle.

## Decision

Every extension must expose an adapter contract and register through the extension registry. The orchestrator communicates with extensions through normalized objects such as `ArtifactRef`, `EvidenceRef`, and budget metadata.

## Consequences

- New features are isolated behind contracts.
- Regression tests can target adapters independently.
- The core harness remains small.
- Some features require wrapper code before they can be used.
