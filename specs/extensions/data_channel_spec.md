# Data Channel Spec

## Purpose

A data channel ingests user-provided or external data and normalizes it into artifacts.

## Contract

```python
class DataChannelAdapter:
    def can_handle(manifest) -> bool: ...
    def normalize(manifest) -> list[ArtifactRef]: ...
    def summarize(artifact) -> EvidenceRef: ...
    def safety_check(artifact) -> SafetyResult: ...
```

## Output Requirement

A channel must output artifact references instead of directly injecting raw data into agent prompts.

## Initial Channels

```text
local_file
csv
json
pdf
image
audio
video
sensor_csv
repo_snapshot
browser_capture
```
