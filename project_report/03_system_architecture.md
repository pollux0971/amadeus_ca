# 03 — System Architecture

Every hop is gated, redacted, and fail-closed; nothing calls a real API or runs a raw
shell.

## Architecture diagram (Mermaid)

```mermaid
flowchart TD
    P[FakeLLMProvider<br/>offline · deterministic · fail-closed<br/>(real provider = planning only)] --> PL[FakePlanner<br/>marker → declarative Plan]
    PL --> PV[PlanValidator<br/>ids/deps/risk · no direct shell · no secret]
    PV --> EB[ExecutionBridge<br/>allowlisted skills · approval · no replan]
    EB --> ORCH[Orchestrator + Safety Gate<br/>command policy per step]
    ORCH --> S1[start_local_server]
    ORCH --> S2[open_localhost_browser<br/>real Playwright]
    ORCH --> S3[read_browser_console]
    ORCH --> S4[patch_file_and_run_tests]
    S1 --> EVAL[Evaluator<br/>trace + score + redacted artifacts]
    S2 --> EVAL
    S3 --> EVAL
    S4 --> EVAL

    EVAL --> RP[Repair proposal<br/>proposal-only]
    RP --> AP[Approved apply<br/>apply workspace only]
    AP --> CM[Candidate merge<br/>candidate workspace only]
    CM --> ST[Staging promotion<br/>staging workspace only + rollback verification]
    ST -.->|BLOCKED: human + policy + rollback + shell-review| STABLE[(stable promotion<br/>NOT STARTED)]

    EVAL --> DASH[Read-only dashboard<br/>redacted snapshot · no actions]
    GATES[Validators / evals<br/>validate_workflows · run_eval · gates] --- ORCH
    GATES --- DASH
```

## Text architecture (fallback)

```
FakeLLMProvider (fake-only, fail-closed; real provider = planning only)
  → FakePlanner → PlanValidator → ExecutionBridge (allowlisted, no replan)
  → Orchestrator + Safety Gate
      → start_local_server / open_localhost_browser (real Playwright) /
        read_browser_console / patch_file_and_run_tests
  → Evaluator (trace + score + redacted artifacts)

Self-evolution chain (all human-gated, workspace-only):
  Repair proposal → Approved apply → Candidate merge → Staging promotion
  → [BLOCKED] stable promotion (human + policy + rollback + shell-execution review)

Cross-cutting: read-only dashboard (redacted snapshot, no actions);
               validators / evals (validate_workflows, run_eval, real-browser + dashboard gates)
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| LLM provider (`src/llm/`) | fake (offline, deterministic); real provider planning-only, fail-closed |
| Planner (`src/planner/`) | marker → declarative plan; validated; never self-executes |
| Execution bridge | runs only allowlisted skills with approval; no autonomous replan |
| Skills | `start_local_server`, `open_localhost_browser` (real Playwright), `read_browser_console`, `patch_file_and_run_tests` |
| Repair (`src/repair/`) | proposal → approved apply → candidate merge → staging (workspace-only, redacted) |
| Orchestrator + Safety Gate | runs sequences; command policy on every step |
| Dashboard (`ui_dashboard/`) | read-only snapshot viewer; no action surface |
| Validators / evals | `validate_workflows` + sub-validators; `run_eval`; real-browser + dashboard smoke gates |
