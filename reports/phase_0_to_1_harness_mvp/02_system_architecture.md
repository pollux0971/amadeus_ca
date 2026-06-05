# 02 · System Architecture

## Text overview

```text
                          ┌─────────────────────────────┐
        eval task (yaml)  │        Orchestrator         │   trace.jsonl
        ───────────────►  │  (run_eval_task: plan,      ├──────────────►  runs/<id>/
                          │   thread blackboard,        │   score.json
                          │   evaluate, teardown)       ├──────────────►  summary.md
                          └─────┬───────────────┬───────┘   failure_report.md
                                │               │
                 selects skill  │               │  per-step trace event
                                ▼               ▼
                   ┌────────────────────┐   ┌──────────────────┐
                   │   Skill Registry   │   │   Trace Logger    │
                   │ (discover/validate │   └──────────────────┘
                   │  skill packages)   │
                   └─────────┬──────────┘
                             │ resolve implementation
                             ▼
                 ┌──────────────────────────────┐
                 │  Candidate Overlay Resolver   │  highest active version
                 │  (stable skill  OR  candidate)│  per overridden skill
                 └───────┬───────────────┬───────┘
                         ▼               ▼
              ┌─────────────────┐  ┌──────────────────┐
              │   CLI Skill     │  │  Browser Skill    │  (server / browser)
              │ (patch, server) │  │ (open localhost)  │
              └───────┬─────────┘  └────────┬─────────┘
                      │ command            │ url
                      ▼                    ▼
              ┌─────────────────┐   ┌──────────────────┐
              │   Safety Gate   │   │  localhost-only   │
              │ (command policy)│   │   URL allowlist   │
              └─────────────────┘   └──────────────────┘

   evaluation: Evidence rules → Evaluator → criteria/forbidden → score.json
   evolution : Candidate workflow → eval → Promotion Gate (human review for
               shell/secret/destructive/browser-trust changes)
```

## Components

- **Orchestrator** (`src/orchestrator/orchestrator.py`) — runs an eval task: builds
  per-skill inputs, threads a shared blackboard across steps, logs a trace event
  per step, evaluates criteria + forbidden actions, writes the run files, and
  tears down kept-alive servers in a `finally`.
- **Skill Registry** (`src/skills_runtime/`) — discovers and validates skill
  packages (manifest, SKILL.md, tests).
- **Candidate Overlay Resolver** (`src/skills_runtime/executor.py`) — for each
  overridden skill, activates the **highest active `version`** candidate under
  `harnesses/candidates/`; otherwise runs the stable skill. The candidate's
  entrypoint is loaded in place of the stable one; the stable package still backs
  domain/risk metadata.
- **CLI Skill** — local-command capabilities (patch + run tests, start server).
- **Browser Skill** — load a localhost URL and snapshot the page.
- **Evaluator** (`src/harness/evaluator.py`) — turns an evidence map into
  criteria results and computes task success (forbidden action ⇒ fail).
- **Trace / Score / Report** (`src/harness/trace_logger.py`) — `trace.jsonl`,
  `score.json`, `summary.md`, `failure_report.md` per run.
- **Safety Gate** (`src/agents/safety_gate/command_policy.py`) — denylist for
  shell commands (`rm -rf`, `sudo`, `cat .env`, `curl|bash`, …). Every command a
  skill runs passes through it.
- **Promotion Gate** (`specs/harness/promotion_policy.md`) — required checks +
  metric gates + human review for shell execution / secrets / destructive ops /
  browser-to-CLI trust changes.
- **Candidate workflow** — changes land as candidates under
  `harnesses/candidates/<id>/`, are exercised via the overlay, evaluated, and
  only then considered for promotion. Each carries a `candidate_summary.md`.

## Stable skill vs candidate skill

| | Stable skill (`skills/<id>/`) | Candidate skill (`harnesses/candidates/<id>/`) |
|---|---|---|
| Role | the promoted, default implementation | an experimental/new version under evaluation |
| Activation | runs unless overridden | overlay activates the highest active version |
| Mutability | protected — not edited directly | where all new work happens |
| Lifecycle | baseline for comparison | dev → staging-ready → (human review) → staging → stable |
| Example here | placeholder `patch_file_and_run_tests` | `patch_file_and_run_tests_v2` (real, plan-driven) |

In this phase the **stable skills, safety gate, and promotion policy were never
modified** — all real implementations live as candidates, exercised through the
overlay.
