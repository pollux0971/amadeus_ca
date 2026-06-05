# 06 · Architecture Diagrams

Mermaid diagrams (render on GitHub or any Mermaid viewer). Reuse any of these in
slides.

## Overall Harness Architecture

```mermaid
flowchart TD
    EVAL[eval task .yaml] --> ORCH[Orchestrator]
    ORCH --> REG[Skill Registry]
    REG --> OVR[Candidate Overlay Resolver]
    OVR -->|stable or candidate| CLI[CLI Skill]
    OVR -->|stable or candidate| BR[Browser Skill]
    CLI --> SG[Safety Gate]
    BR --> LH[localhost-only URL check]
    ORCH --> TR[Trace Logger]
    TR --> RUN[(runs/&lt;id&gt;: trace.jsonl / score.json / summary.md)]
    ORCH --> EVALR[Evaluator]
    EVALR --> SCORE[score.json]
    ORCH --> PROMO[Promotion Gate / human review]
```

## Candidate Overlay Flow

```mermaid
flowchart LR
    Q{override active\nfor skill?} -->|no| STABLE[run stable skills/&lt;id&gt;]
    Q -->|yes| PICK[pick highest active version]
    PICK --> LOAD[load candidate entrypoint]
    LOAD --> RUN2[execute candidate]
    STABLE --> RUN2
```

## Skill Execution Flow

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant X as Executor (overlay)
    participant S as Skill
    participant G as Safety Gate
    O->>X: build inputs (blackboard)
    X->>S: run(inputs)
    S->>G: check_command(cmd)
    G-->>S: allowed / blocked
    S-->>X: output (status, refs, ...)
    X-->>O: result
    O->>O: trace event + evidence
    O->>O: evaluator -> score.json
```

## Patch Runner Flow (patch_file_and_run_tests_v2)

```mermaid
flowchart TD
    PLAN[patch_plan: replace_text / unified_diff] --> COPY[sandbox copy of fixture]
    COPY --> APPLY[apply patches in sandbox]
    APPLY --> DIFF[emit patch.diff]
    APPLY --> TEST[run test_command via Safety Gate]
    TEST --> RES[result.json: patch_applied / test_passed / failure_reason]
    COPY -. source fixture never mutated .-> SRC[(fixtures/...)]
```

## Server Keep-Alive Handoff Flow (start_local_server_v1.2)

```mermaid
flowchart TD
    START[start_local_server keep_alive=true] --> URL[detect localhost URL]
    URL --> SESS[emit server_session.json + register in _sessions]
    SESS --> NEXT[later skill uses server_url]
    NEXT --> END{run end}
    END --> TEARDOWN[orchestrator finally: killpg + remove sandbox + deregister]
    SESS -. crash before teardown .-> REAP[lease reaper: reap stale by started_at+lease_ttl_sec]
```

## Browser Gate Flow

```mermaid
flowchart TD
    MODE{browser_mode} -->|playwright| PW{Playwright + Chromium?}
    PW -->|yes| REAL[real browser load: engine=playwright, is_real_browser=true]
    PW -->|no| MISS[browser_runtime_missing]
    MODE -->|auto| PW2{Playwright?}
    PW2 -->|yes| REAL
    PW2 -->|no| FB[http_fallback: NOT a real browser, is_real_browser=false]
    MODE -->|http_fallback| FB
    REAL --> GATE[run_playwright_gate.py / run_full_browser_gate.py]
```

## Promotion Gate Flow

```mermaid
flowchart LR
    CAND[candidate dev] --> EVALG[evals pass?]
    EVALG -->|no| CAND
    EVALG -->|yes| READY[staging-ready]
    READY --> HR{human review needed?\nshell / secrets / destructive / browser-trust}
    HR -->|yes, sign-off| STAGING[staging]
    HR -->|no| STAGING
    STAGING --> OBS[observe] --> STABLE[stable - separate decision]
```
