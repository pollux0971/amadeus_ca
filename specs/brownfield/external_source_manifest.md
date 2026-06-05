# External Source Manifest Schema

## Purpose

A manifest describes a dataset, open-source project, UI prototype, multimodal file, or other brownfield source before it enters the harness.

## YAML Shape

```yaml
source_id: browser_use_repo_001
source_type: repo
origin: third_party_open_source
location: external/inbox/raw/browser-use
license: MIT
trust_level: third_party_open_source
intended_use:
  - reference_implementation
  - adapter_design
allowed_operations:
  - read_files
  - run_tests_in_sandbox
forbidden_operations:
  - execute_install_scripts_without_review
  - read_secrets
  - modify_stable_harness
owner: user
review_status: manifested
notes: "Use as reference, do not vendor into src/ directly."
```

## Required Fields

- `source_id`
- `source_type`
- `origin`
- `location`
- `trust_level`
- `intended_use`
- `allowed_operations`
- `review_status`

## Source Types

```text
repo
archive
dataset
document
image
audio
video
sensor_stream
ui_prototype
api_spec
browser_capture
```

## Review Status

```text
manifested
quarantined
normalized
staged
tested
approved
rejected
deprecated
```
