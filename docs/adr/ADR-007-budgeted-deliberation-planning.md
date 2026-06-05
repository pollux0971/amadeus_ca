# ADR-007: Budgeted Deliberation Planning

## Status

Accepted.

## Context

Structured planning improves reliability, but unbounded planning increases token cost and latency. This project needs planning that is both reliable and cost-aware.

## Decision

The planner uses budgeted deliberation:

- maximum recursion depth,
- maximum replan count,
- maximum retry count,
- local repair before global replan,
- simple direct execution for simple tasks.

## Consequences

- ReCAP-style parent plan reinjection remains useful.
- GraSP-style DAG execution remains useful.
- Both must be bounded by explicit budget policy.
