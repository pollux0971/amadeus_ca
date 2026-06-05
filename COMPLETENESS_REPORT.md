# Completeness Report

## Status

Updated after adding Brownfield + Harness workflow support for future full-stack UI, external source intake, data channels, and multimodal extensions.

## Structure Check

Expected major directories:

- `docs/`
- `docs/adr/`
- `specs/harness/`
- `specs/skills/`
- `specs/evals/`
- `specs/brownfield/`
- `specs/extensions/`
- `src/harness/`
- `src/skills_runtime/`
- `src/orchestrator/`
- `skills/`
- `evals/`
- `fixtures/`
- `external/`
- `apps/`
- `scripts/`
- `tests/`

## Added in Brownfield Update

### Documents

- `docs/11_brownfield_harness_workflow.md`
- `docs/12_extension_roadmap.md`
- `docs/13_multimodal_and_data_channels.md`
- `docs/adr/ADR-009-brownfield-external-source-intake.md`
- `docs/adr/ADR-010-extension-adapter-contract.md`
- `docs/adr/ADR-011-fullstack-ui-as-separate-surface.md`
- `docs/adr/ADR-012-multimodal-as-normalized-artifacts.md`

### Specs

- `specs/brownfield/brownfield_workflow.md`
- `specs/brownfield/external_source_manifest.md`
- `specs/brownfield/feature_intake_spec.md`
- `specs/extensions/extension_adapter_spec.md`
- `specs/extensions/data_channel_spec.md`
- `specs/extensions/multimodal_extension_spec.md`
- `specs/extensions/fullstack_interface_extension.md`
- `specs/extensions/integration_gate_policy.md`

### Runtime Skeletons

- `src/harness/source_manifest.py`
- `src/harness/extension_registry.py`
- `src/harness/brownfield_intake.py`
- `src/harness/multimodal_artifacts.py`
- `src/harness/data_channel.py`

### Fixed Intake Locations

- `external/inbox/raw/`
- `external/inbox/manifests/`
- `external/staging/`
- `external/approved/`
- `external/projects/`
- `external/datasets/`
- `external/multimodal/`

### Future UI Surface

- `apps/web_console/README.md`
- `apps/web_console/API_CONTRACT.md`
- `apps/web_console/package.json`

### New Evals

- `evals/brownfield/fullstack_ui_extension.yaml`
- `evals/brownfield/new_data_channel_csv_ingest.yaml`
- `evals/brownfield/open_source_project_intake.yaml`
- `evals/multimodal/image_input_channel_smoke.yaml`
- `evals/multimodal/pdf_artifact_extraction.yaml`

## Conflict Review

No existing design was invalidated. The update makes the project more conservative:

- External projects are not vendored into `src/` directly.
- Full-stack UI is treated as a separate app surface under `apps/`.
- New data and multimodal inputs become `ArtifactRef` objects before entering context.
- Runtime agents use approved adapters, not arbitrary filesystem access.
- Efficiency budgets still apply to new extensions.

## Test Status

Run:

```bash
python scripts/validate_structure.py
pytest -q
python scripts/run_skill_tests.py
```

Expected status after this update:

- structure validation passes,
- unit tests pass,
- existing skill tests pass.


## Final Workflow Audit Update

Added explicit start-from-zero and scale-out workflow documents after final review.

### Added 0→1 / 1→N Files

- `START_HERE.md`
- `WORKFLOW_INDEX.md`
- `docs/14_zero_to_one_workflow.md`
- `docs/15_one_to_n_workflow.md`
- `specs/workflows/zero_to_one_contract.md`
- `specs/workflows/one_to_n_contract.md`
- `scripts/validate_workflows.py`
- `templates/feature_intake/feature_intake_template.yaml`
- `templates/eval_task/eval_task_template.yaml`
- `templates/extension_adapter/adapter_template.md`
- `templates/skill_package/SKILL_TEMPLATE.md`

### Final Judgment

The previous brownfield update contained the right concepts, but the 0→1 and 1→N paths were not separated explicitly enough for a from-scratch implementation. This update makes the two workflows first-class documents and adds a validator to prevent them from being accidentally removed.

### Required Final Checks

```bash
python scripts/validate_structure.py
python scripts/validate_workflows.py
pytest -q
python scripts/run_skill_tests.py
```
