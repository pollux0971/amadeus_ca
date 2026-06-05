# Workflow Index

This index explains which workflow to use.

## Use 0→1 when...

You are building the first working harness from scratch.

Read:

```text
docs/14_zero_to_one_workflow.md
specs/workflows/zero_to_one_contract.md
START_HERE.md
```

## Use 1→N when...

You already have a working harness and want to add:

```text
full-stack UI
data channel
multimodal input
external open-source project
new browser backend
new skill family
new agent role
new benchmark suite
```

Read:

```text
docs/15_one_to_n_workflow.md
docs/11_brownfield_harness_workflow.md
specs/workflows/one_to_n_contract.md
specs/extensions/extension_adapter_spec.md
```

## Quick Decision Table

| Situation | Workflow | First File to Create |
|---|---|---|
| Empty repo, first demo | 0→1 | `docs/00_project_brief.md` |
| Add new skill | 1→N | `templates/feature_intake/feature_intake_template.yaml` |
| Add full-stack UI | 1→N | `feature_intake.yaml` + `apps/web_console/API_CONTRACT.md` |
| Add CSV/PDF/Image input | 1→N | `external_source_manifest.yaml` |
| Add GitHub repo | 1→N | `external_source_manifest.yaml` |
| Change Safety Gate | 1→N high-risk | `risk_report.md` + manual review |
