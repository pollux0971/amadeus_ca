# Plan

- goal: Create a safe read-only two-step project inspection plan:
1. inspect_project
2. list_project_files
Do not execute anything.
- marker: (none)
- steps: 2
- valid: True

| id | skill | depends_on | risk | approval | success_criteria |
| --- | --- | --- | --- | --- | --- |
| inspect | inspect_project | - | low | no | project_inspected |
| list_files | list_project_files | inspect | low | no | files_listed |

> Plan only — the planner never executes these steps.
