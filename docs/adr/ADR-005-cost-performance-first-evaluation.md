# ADR-005: Cost-Performance-First Evaluation

## Status

Accepted.

## Context

The efficient-agents survey argues that agent efficiency should be evaluated as a cost-performance trade-off, not simply as model size or final accuracy. Agent systems incur extra costs from memory access, tool calls, retries, and planning.

## Decision

Every benchmark run must report both success and cost.

Required fields:

```yaml
task_success: bool
score: float
total_steps: int
cli_command_count: int
browser_action_count: int
tool_call_count: int
retry_count: int
runtime_sec: float
context_tokens_estimated: int
budget_violation_count: int
cost_of_success: float | null
```

## Consequences

- A slower or more verbose agent can be considered worse even if it succeeds.
- Candidate harnesses must be compared by Pareto-style trade-off when possible.
- The demo report must show at least one baseline-vs-candidate efficiency table.
