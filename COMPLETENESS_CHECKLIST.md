# Completeness Checklist

## Documentation

- [x] README
- [x] Project brief
- [x] Problem definition
- [x] System overview
- [x] Glossary
- [x] Development roadmap
- [x] Demo plan
- [x] Evaluation plan
- [x] Risk and safety
- [x] Research notes
- [x] ADRs

## Specs

- [x] Harness contract
- [x] Context packet schema
- [x] Trace schema
- [x] Scoring schema
- [x] Promotion policy
- [x] Skill package spec
- [x] Manifest schema
- [x] Gene schema
- [x] Skill graph schema
- [x] Skill lifecycle
- [x] Benchmark task schema
- [x] Gherkin guide
- [x] Test levels
- [x] Failure taxonomy

## Runtime Skeleton

- [x] Skill loader
- [x] Skill validator
- [x] Skill registry
- [x] Trace logger
- [x] Safety gate
- [x] CLI command runner
- [x] Browser controller placeholder
- [x] Orchestrator placeholder
- [x] Evaluator placeholder

## Skills

- [x] inspect_project
- [x] start_local_server
- [x] open_localhost_browser
- [x] read_browser_console
- [x] patch_file_and_run_tests

## Evals

- [x] CLI-only task
- [x] Browser/CLI integration task
- [x] Adversarial prompt injection task
- [x] Sharded multi-turn task

## Fixtures

- [x] Python bug project
- [x] Vite login bug project
- [x] Malicious README project
- [x] Browser prompt injection page

## Known TODO

- [ ] Replace browser placeholder with Playwright or browser-use.
- [ ] Replace placeholder orchestrator with real skill DAG execution.
- [ ] Implement real patch application.
- [ ] Implement candidate repair loop with Claude Code / Codex.
- [ ] Add dashboard or report visualization.
