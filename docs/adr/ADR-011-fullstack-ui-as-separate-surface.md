# ADR-011: Full-Stack UI as a Separate Surface

## Status

Accepted.

## Context

A future web dashboard is useful for viewing runs, traces, skills, and candidate patches. However, UI code should not become part of the agent core.

## Decision

The full-stack UI is placed under `apps/` and communicates with the harness through stable API endpoints. It must not directly mutate stable skills, safety policies, or promotion rules.

## Consequences

- UI can evolve independently.
- The harness remains testable without the UI.
- The UI can trigger evals and create intake manifests, but promotion remains governed by policy.
