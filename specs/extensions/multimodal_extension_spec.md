# Multimodal Extension Spec

## Purpose

This spec defines how multimodal inputs are represented, processed, and exposed to agents.

## Core Rule

Raw multimodal files are stored as artifacts. Agents receive metadata and selected evidence, not raw dumps.

## Artifact Types

```text
image
pdf
audio
video
sensor_stream
screenshot
scan
```

## Required Metadata

```yaml
artifact_id: string
artifact_type: string
uri: string
sha256: string | null
mime_type: string | null
trust_level: string
summary: string
metadata: object
raw_ref: string
```

## Processing Stages

1. Validate file type.
2. Compute hash when possible.
3. Extract metadata.
4. Produce summary or derived features.
5. Create evidence refs.
6. Route into context only when task-relevant.
