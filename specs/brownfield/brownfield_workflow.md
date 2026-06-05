# Brownfield Workflow Specification

## State Machine

```text
new_source
  → manifested
  → quarantined
  → normalized
  → staged
  → tested
  → approved
  → enabled
  → deprecated
```

## Required Artifacts

Every brownfield addition requires:

- `source_manifest.yaml`
- feature proposal or adapter spec
- fixture or sample source
- unit tests
- integration or eval task
- safety review
- rollback plan

## Gates

### Manifest Gate

The source must declare type, origin, license, trust level, intended use, and allowed operations.

### Safety Gate

The source is scanned for secrets, dangerous scripts, executable install hooks, and prompt injection content when applicable.

### Adapter Gate

The source must be accessed through an adapter. Direct runtime access to arbitrary source folders is not allowed.

### Evaluation Gate

The extension must pass its eval task under budget.

### Promotion Gate

Only approved sources can be visible to runtime agents.

## Brownfield Change Categories

```text
small_patch       changes an existing module without new source type
new_skill         adds a skill package
new_channel       adds a data input adapter
new_modality      adds multimodal artifact support
new_interface     adds UI / API / app surface
external_project  imports third-party code or reference repo
```
