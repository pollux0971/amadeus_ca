# Web Console Extension Skeleton

This is a placeholder for a future full-stack interface.

## Purpose

The web console should help users inspect:

- run traces,
- score reports,
- skill registry entries,
- eval tasks,
- candidate patches,
- external source intake status.

## Boundary

The UI must not directly mutate stable harness internals. It should use the API contract in `API_CONTRACT.md`.

## First MVP

Read-only pages:

1. Runs list.
2. Single run report.
3. Skill registry list.
4. External intake queue.

Write actions come later and must go through candidates and promotion policy.
