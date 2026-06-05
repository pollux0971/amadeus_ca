from __future__ import annotations

from pathlib import Path
import sys


REQUIRED_PATHS = [
    "START_HERE.md",
    "WORKFLOW_INDEX.md",
    "docs/14_zero_to_one_workflow.md",
    "docs/15_one_to_n_workflow.md",
    "specs/workflows/zero_to_one_contract.md",
    "specs/workflows/one_to_n_contract.md",
    "templates/feature_intake/feature_intake_template.yaml",
    "templates/eval_task/eval_task_template.yaml",
    "templates/extension_adapter/adapter_template.md",
    "templates/skill_package/SKILL_TEMPLATE.md",
    "scripts/validate_workflows.py",
    "README.md",
    "docs/00_project_brief.md",
    "docs/01_problem_definition.md",
    "docs/02_system_overview.md",
    "docs/03_glossary.md",
    "docs/04_development_roadmap.md",
    "docs/05_demo_plan.md",
    "docs/06_evaluation_plan.md",
    "docs/07_risk_and_safety.md",
    "specs/harness/harness_contract.md",
    "specs/harness/context_packet_schema.md",
    "specs/harness/trace_schema.md",
    "specs/harness/scoring_schema.md",
    "specs/harness/promotion_policy.md",
    "specs/skills/skill_package_spec.md",
    "specs/skills/manifest_schema.md",
    "specs/skills/gene_schema.md",
    "specs/skills/skill_graph_schema.md",
    "specs/skills/skill_lifecycle.md",
    "specs/evals/benchmark_task_schema.md",
    "specs/evals/test_levels.md",
    "src/skills_runtime/loader.py",
    "src/skills_runtime/validator.py",
    "src/skills_runtime/registry.py",
    "src/harness/trace_logger.py",
    "src/orchestrator/orchestrator.py",
    "skills/inspect_project/SKILL.md",
    "evals/cli_browser_integration/vite_login_bug.yaml",
    "evals/multimodal/pdf_artifact_extraction.yaml",
    "evals/multimodal/image_input_channel_smoke.yaml",
    "evals/brownfield/open_source_project_intake.yaml",
    "evals/brownfield/new_data_channel_csv_ingest.yaml",
    "evals/brownfield/fullstack_ui_extension.yaml",
    "src/harness/data_channel.py",
    "src/harness/multimodal_artifacts.py",
    "src/harness/brownfield_intake.py",
    "src/harness/extension_registry.py",
    "src/harness/source_manifest.py",
    "apps/web_console/API_CONTRACT.md",
    "apps/README.md",
    "external/inbox/manifests/example_source_manifest.yaml",
    "external/README.md",
    "specs/extensions/integration_gate_policy.md",
    "specs/extensions/fullstack_interface_extension.md",
    "specs/extensions/multimodal_extension_spec.md",
    "specs/extensions/data_channel_spec.md",
    "specs/extensions/extension_adapter_spec.md",
    "specs/brownfield/feature_intake_spec.md",
    "specs/brownfield/external_source_manifest.md",
    "specs/brownfield/brownfield_workflow.md",
    "docs/13_multimodal_and_data_channels.md",
    "docs/12_extension_roadmap.md",
    "docs/11_brownfield_harness_workflow.md",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing = [p for p in REQUIRED_PATHS if not (root / p).exists()]
    if missing:
        print("[FAIL] missing required paths:")
        for p in missing:
            print(f"  - {p}")
        return 1
    print("[PASS] project structure is complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
