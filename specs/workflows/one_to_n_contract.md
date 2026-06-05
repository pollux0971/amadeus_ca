# One-to-N Workflow Contract

This contract defines how new capabilities are added after the first stable harness exists.

## Required Gates

| Gate | Required Output | Applies To |
|---|---|---|
| Feature Intake | `feature_intake.yaml` | all new features |
| Source Manifest | `source_manifest.yaml` | external data/projects/assets |
| Brownfield Inspection | `inspection_report.md` | external projects, code, datasets |
| Adapter Contract | adapter spec or class | all runtime integrations |
| Contract Tests | unit tests | all adapters |
| Eval Task | `evals/**/<task>.yaml` | all user-visible features |
| Safety Review | risk report | CLI/browser/network/secrets |
| Budget Review | score/budget fields | tool, context, runtime-heavy features |
| Promotion Decision | dev/staging/stable | all candidates |

## Change Types

```text
new_skill
new_data_channel
new_multimodal_channel
new_fullstack_ui
new_agent_role
new_browser_backend
new_external_project
new_harness_policy
```

## Required Candidate Artifacts

```text
candidate_summary.md
changed_files.txt
tests_run.txt
risk_report.md
rollback_plan.md
```

## Forbidden Shortcuts

- Do not copy external source directly into core runtime.
- Do not expose shell execution through UI.
- Do not promote high-risk changes automatically.
- Do not remove safety checks to pass tests.
- Do not add a data channel without artifact references.
- Do not add a multimodal input path that injects raw binary into prompt context.

## Done Definition

A one-to-N feature is done only if it is adapter-based, testable, traceable, budget-aware, safe, and rollbackable.
