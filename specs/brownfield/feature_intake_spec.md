# Feature Intake Spec

## Purpose

Before implementing a new feature, write a feature intake note. This prevents uncontrolled brownfield growth.

## Template

```yaml
feature_id: web_console_v1
category: new_interface
summary: "Read-only dashboard for runs, skills, and eval reports."
entry_points:
  - apps/web_console
external_sources:
  - source_id: dashboard_template_001
runtime_surfaces:
  - api
  - web_ui
required_adapters:
  - run_report_reader
  - skill_registry_reader
required_evals:
  - evals/brownfield/fullstack_ui_extension.yaml
risk_level: medium
rollback_plan: "Disable extension in extension_registry.yaml"
```

## Required Questions

1. What user workflow improves?
2. Which existing harness modules are touched?
3. What new context or tool cost is introduced?
4. What new safety risk is introduced?
5. What exact eval proves it works?
6. How can it be disabled?
