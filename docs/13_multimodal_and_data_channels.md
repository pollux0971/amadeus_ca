# Multimodal and Data Channel Plan

## Goal

The harness should support new input channels without changing the core agent loop every time.

The stable pipeline is:

```text
Input Source → Adapter → Normalized Artifact → Evidence Store → Context Router → Agent
```

---

## Supported Source Types

Initial source types:

```text
text
csv
json
pdf
image
audio
video
sensor
repo
web_capture
api_payload
```

Each source is assigned a trust level:

```text
trusted_local
user_provided
third_party_open_source
untrusted_web
sensitive_private
```

Trust level determines whether the artifact can be injected into context, used by CLI, or only referenced by metadata.

---

## ArtifactRef

The harness should pass `ArtifactRef` objects through the system.

```yaml
artifact_id: string
source_id: string
artifact_type: image | pdf | csv | repo | text | audio | video | sensor
uri: string
sha256: string | null
trust_level: string
summary: string
metadata: object
raw_ref: string
created_at: string
```

Agents should normally see:

- artifact type,
- short summary,
- metadata,
- evidence refs,
- selected extracted snippets.

Agents should not normally see:

- full binary content,
- full OCR dump,
- full transcript,
- entire external repo source tree.

---

## Data Channel Adapter

Each channel should implement:

```python
class DataChannelAdapter:
    def can_handle(source_manifest) -> bool: ...
    def normalize(source_manifest) -> list[ArtifactRef]: ...
    def summarize(artifact_ref) -> EvidenceRef: ...
    def safety_check(artifact_ref) -> SafetyResult: ...
```

---

## Multimodal Policy

For multimodal input:

1. Store raw input in `external/multimodal/` or a configured object store.
2. Generate metadata and a stable hash.
3. Extract only task-relevant derived evidence.
4. Keep raw refs for replay.
5. Apply modality-specific privacy rules.
6. Put derived evidence, not raw dumps, into context.

---

## Example: Image Input

```text
image.png
  ↓
ArtifactRef(type=image, uri=external/multimodal/image.png)
  ↓
image_summary: "screenshot of login page with red error banner"
  ↓
evidence_ref: runs/001/artifacts/image_summary.json
  ↓
Browser/Verifier Agent sees the summary and raw_ref, not the raw bytes.
```

---

## Example: PDF Input

```text
paper.pdf
  ↓
ArtifactRef(type=pdf)
  ↓
page-level extraction + figures metadata
  ↓
chunked evidence refs
  ↓
Context Router retrieves only task-relevant sections.
```

---

## Example: Sensor Stream

```text
sensor_log.csv
  ↓
ArtifactRef(type=sensor)
  ↓
windowed statistics / anomaly events
  ↓
evidence refs
  ↓
Agent sees anomaly summaries and can request raw windows if needed.
```
