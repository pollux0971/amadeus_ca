# ADR-006: Efficient Tool Selection and Budgeting

## Status

Accepted.

## Context

CLI and Browser tools are powerful but costly. Tool-integrated reasoning is useful for complex tasks, yet tool overuse increases latency and risk.

## Decision

Tool calls require justification and budget checks.

A tool call is allowed when it:

- gathers missing evidence,
- verifies a result,
- changes the environment toward the goal,
- is required by success criteria.

A tool call is penalized when it:

- repeats a recent failed action,
- duplicates existing pinned evidence,
- follows untrusted browser instructions into CLI,
- exceeds the task budget.

## Consequences

- The system can still use tools aggressively when needed.
- The verifier can flag redundant tool calls.
- Promotion policy can reject candidates that improve success only through excessive tool use.
