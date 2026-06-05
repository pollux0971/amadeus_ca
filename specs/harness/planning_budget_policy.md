# Planning Budget Policy

## Purpose

Planning is useful but not free. This policy prevents unbounded reasoning, repeated replanning, and multi-agent over-coordination.

---

## Default Planning Budget

```yaml
planning_budget:
  max_plan_depth: 4
  max_replan_count: 5
  max_retry_per_skill: 2
  max_dag_nodes: 12
  max_parallel_branches: 2
  max_agent_handoffs: 8
```

---

## Planning Modes

### direct

Use for simple tasks with known skill path.

### recap

Use when the task is long and needs parent-plan reinjection.

### skill_dag

Use when skill dependencies are known.

### reactive_fallback

Use when skill confidence is low or DAG compilation fails.

---

## Replanning Rules

Replan only when:

- a skill fails,
- a precondition is not satisfied,
- new evidence invalidates the current plan,
- Safety Gate blocks a planned action,
- verifier says success criteria are incomplete.

Do not replan merely because the agent is uncertain; first collect targeted evidence.

---

## Local Repair Before Global Replan

If a DAG node fails:

1. retry if failure is transient,
2. rebind arguments if inputs are wrong,
3. insert prerequisite if precondition is missing,
4. substitute skill if schema is incompatible,
5. globally replan only if local repair fails.
