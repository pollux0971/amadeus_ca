# Zero-to-One Workflow Contract

This contract defines the required gates for building the first working version of the agent harness from scratch.

## Required Gates

| Gate | Required Output | Blocking? |
|---|---|---:|
| G0 Repo Skeleton | Required directories and docs exist | Yes |
| G1 Skill Registry | `.cache/skill_registry.json` generated | Yes |
| G2 Trace Logging | `runs/<run_id>/trace.jsonl` generated | Yes |
| G3 CLI Safety | Dangerous commands blocked | Yes |
| G4 Browser Smoke | Localhost/fixture page can be opened | Yes |
| G5 Evaluation | `score.json` generated | Yes |
| G6 Vertical Slice | `vite_login_bug` demo completes | Yes |

## Minimum Core Skills

```text
inspect_project
start_local_server
open_localhost_browser
read_browser_console
patch_file_and_run_tests
```

## Required Commands

```bash
pytest -q
python scripts/validate_structure.py
python scripts/validate_workflows.py
python scripts/run_skill_tests.py
python scripts/run_demo.py --demo vite_login_bug
```

## Forbidden Shortcuts

- Do not bypass the trace logger.
- Do not mark a task as successful without verifier output.
- Do not run unrestricted shell commands.
- Do not add external projects directly into `src/`.
- Do not inject full raw logs into the runtime prompt.

## Done Definition

Zero-to-one is done when the system can execute one CLI + Browser task end-to-end and produce trace, score, and report artifacts.
