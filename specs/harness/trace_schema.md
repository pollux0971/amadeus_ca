# Trace Schema

每次 agent 行動都必須產生 trace event。  
Trace 是後續 evaluation、debug、repair、promotion 的核心資料。

```yaml
trace_event:
  task_id: string
  run_id: string
  step_id: string
  timestamp: string

  actor:
    agent_id: string
    skill_id: string | null
    tool_name: string | null

  input:
    context_packet_ref: string | null
    user_visible_goal: string
    tool_call:
      name: string
      args: object

  output:
    observation: string
    artifacts:
      - path: string
        type: log | screenshot | json | text | patch | report
    error:
      type: string | null
      message: string | null

  evaluation:
    step_success: boolean | null
    verifier_result: string | null
    confidence: float | null

  safety:
    risk_level: low | medium | high
    blocked: boolean
    block_reason: string | null

  cost:
    tokens_in: integer | null
    tokens_out: integer | null
    wall_time_ms: integer
```

## Required Run Files

```text
runs/<run_id>/
├── task.yaml
├── trace.jsonl
├── score.json
├── summary.md
├── failure_report.md
├── artifacts/
├── cli.log
└── browser/
```
