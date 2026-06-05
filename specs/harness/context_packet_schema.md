# Context Packet Schema

Context Packet 是每一步傳給 agent 的結構化上下文。  
不要把所有歷史塞進 prompt；只放當前任務需要的最小資訊。

```yaml
context_packet:
  header:
    task_id: string
    run_id: string
    step_id: string
    agent_id: string
    risk_level: low | medium | high

  goal:
    original_user_goal: string
    current_subgoal: string
    success_criteria:
      - string

  plan:
    parent_plan:
      - string
    completed_steps:
      - string
    remaining_steps:
      - string

  state:
    shared_blackboard:
      current_url: string | null
      server_url: string | null
      changed_files:
        - string
      verified_evidence:
        - evidence_id: string
          summary: string
    agent_private_state:
      type: object

  retrieved:
    skill_genes:
      - skill_id: string
        summary: string
        strategy:
          - string
        avoid:
          - string
        validation:
          - string
    evidence_refs:
      - id: string
        path: string
        summary: string
    memory_notes:
      - string

  safety:
    allowed_tools:
      - string
    denied_actions:
      - string
    untrusted_sources:
      - source_id: string
        reason: string

  output_schema:
    format: json
    required_fields:
      - status
      - observations
      - artifacts
      - next_recommendation
```

## Rules

- Browser raw DOM should be summarized before injection.
- CLI logs should be clipped or summarized.
- Secrets must never appear in context packet.
- Skill `SKILL.md` should not be injected by default; use `gene.yaml`.
- Parent plan should be re-injected after subtask completion.
