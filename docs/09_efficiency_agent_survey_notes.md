# Efficient Agents Survey Notes

Source paper: **Toward Efficient Agents: A Survey of Memory, Tool learning, and Planning** (`2601.14192v1.pdf`).

This document records how the survey changes this project. The survey is useful because it reframes this project from simply building a capable agent into building a **cost-aware agent harness**.

---

## 1. Core Takeaway

The survey's most important claim for this project is:

> An efficient agent is not merely a smaller model. It is an agentic system that maximizes task success while minimizing resource consumption across memory, tool use, and planning.

For this project, that means the demo should not only prove that the agent can repair a browser/CLI task. It should also report:

- how many steps were taken,
- how many CLI commands were executed,
- how many browser actions were taken,
- how many tool calls were avoided,
- how much context was injected,
- how many retries occurred,
- whether the same success can be achieved under a smaller budget.

This changes the project's evaluation direction from:

```text
Can the agent finish the task?
```

to:

```text
Can the agent finish the task reliably under an explicit cost budget?
```

---

## 2. How the Survey Maps to This Project

The survey divides efficient agents into three major components:

```text
Memory  -> Context
Planning -> Decision
Tool Learning -> Action
Observation -> Feedback
```

This project maps them as follows:

| Survey Component | Project Component | Concrete Files |
|---|---|---|
| Efficient Memory | Context Router, Sensory Filter, Evidence Store | `src/harness/context_router.py`, `src/harness/sensory_filter.py` |
| Efficient Tool Learning | Skill selection, tool budget, CLI/browser action control | `specs/harness/tool_budget_policy.md` |
| Efficient Planning | Budgeted deliberation, step limit, retry control | `specs/harness/planning_budget_policy.md` |
| Efficiency Evaluation | score.json, efficiency report, Pareto comparison | `src/harness/efficiency.py`, `specs/harness/efficiency_metrics.md` |

---

## 3. New Design Principle: Cost Must Be First-Class State

Before this update, the project tracked task success, safety, and trace. After this update, every run should also track an explicit cost state.

```yaml
budget_state:
  max_steps: 30
  max_cli_commands: 10
  max_browser_actions: 20
  max_retries: 3
  max_context_tokens: 12000
  max_wall_time_sec: 600

current_cost:
  total_steps: 0
  cli_command_count: 0
  browser_action_count: 0
  retries: 0
  context_tokens_estimated: 0
  wall_time_sec: 0
```

The orchestrator should check this state before deciding the next action.

---

## 4. Memory / Context Lessons

The survey's memory section is consistent with LightMem and AgentSwing:

- Naively appending raw history is inefficient.
- Context length can increase cost and reduce accuracy.
- Memory should be constructed, managed, and accessed selectively.
- Multi-agent systems need role-aware memory routing.

Project decision:

```text
Do not inject full trace into prompts.
Do not inject full SKILL.md into runtime prompts.
Use gene.yaml, pinned evidence, and compressed observations.
Keep raw logs as artifacts and inject only references plus short summaries.
```

---

## 5. Tool Learning Lessons

The survey emphasizes that tool use is not free. Tool-integrated reasoning is valuable for complex tasks involving browsers, search APIs, and code interpreters, but unnecessary tools increase latency and system complexity.

Project decision:

```text
The agent must justify tool use.
Each tool call must be logged and scored.
Redundant tool calls should reduce efficiency score.
Browser-to-CLI tool handoff must pass Safety Gate.
```

Useful rule:

```text
Use tools when they reduce uncertainty or provide verification.
Do not use tools merely because they are available.
```

---

## 6. Planning Lessons

The survey treats efficient planning as a resource-constrained control problem. This aligns with ReCAP and GraSP, but adds an explicit cost layer.

Project decision:

```text
Planning should be budget-aware.
The planner must stop expanding the plan when the marginal value of more planning is lower than the cost.
```

For MVP, implement this as simple rules:

- stop after repeated failure loops,
- limit replanning count,
- prefer local repair before global replanning,
- use ReCAP-style parent plan reinjection but not unlimited recursion,
- use GraSP-style DAG execution when dependencies are clear,
- fall back to simple ReAct only when skill confidence is low.

---

## 7. New Metrics to Add

The survey suggests efficiency should be measured as a cost-performance trade-off, not a single accuracy number. This project should therefore report:

```yaml
primary:
  task_success: bool
  score: float

efficiency:
  total_steps: int
  cli_command_count: int
  browser_action_count: int
  tool_call_count: int
  retry_count: int
  runtime_sec: float
  context_tokens_estimated: int
  cost_of_success: float
  budget_violation_count: int

quality:
  failure_recovery_rate: float
  redundant_tool_call_count: int
  unnecessary_replanning_count: int
  evidence_precision: float
```

---

## 8. Critical Limitation

The survey is a survey, not a system paper. It provides taxonomy and evaluation principles, but it does not directly tell us how to implement a CLI/browser harness. Therefore:

- use it to structure evaluation,
- use it to justify budget-aware design,
- do not overclaim that it validates this project architecture,
- do not treat every cited method as compatible with the MVP.

---

## 9. Concrete Project Updates Introduced

This update adds:

```text
specs/harness/efficiency_metrics.md
specs/harness/tool_budget_policy.md
specs/harness/planning_budget_policy.md
specs/harness/memory_policy.md
src/harness/efficiency.py
src/harness/context_router.py
src/harness/sensory_filter.py
evals/efficiency/*
docs/10_conflict_and_staleness_review.md
```
