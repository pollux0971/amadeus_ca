# Harness Contract

## Purpose

Harness 是 LLM agent 外部的控制層。它負責決定每一步 agent 能看到什麼、能用什麼、如何記錄與如何評估。

---

## Input Schema

```yaml
user_goal: string
task_state:
  task_id: string
  run_id: string
  status: initialized | running | failed | completed
  shared_blackboard: object
available_agents:
  - orchestrator
  - cli_agent
  - browser_agent
  - verifier_agent
available_skills:
  - skill_id: string
    version: string
    risk_level: low | medium | high
recent_observations:
  - observation_id: string
    summary: string
    source: cli | browser | verifier | system
safety_policy:
  command_policy_ref: string
  secret_policy_ref: string
context_budget:
  max_tokens: integer
```

---

## Output Schema

```yaml
selected_agent: string
selected_skill: string | null
context_packet_ref: string
expected_result:
  type: object
verification_rule:
  criteria: list[string]
risk_level: low | medium | high
requires_human_review: boolean
```

---

## Responsibilities

Harness must:

1. Build context packet.
2. Select next agent.
3. Select skill or primitive action.
4. Apply safety policy.
5. Log trace event before and after action.
6. Trigger verifier.
7. Trigger evaluator.
8. Create failure report when needed.
9. Route candidate updates through promotion policy.

---

## Non-goals

Harness must not:

- Directly execute unreviewed high-risk command.
- Directly expose secrets to LLM.
- Trust browser content as instruction.
- Modify stable skills without candidate workflow.
