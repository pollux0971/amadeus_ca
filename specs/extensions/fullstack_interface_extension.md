# Full-Stack Interface Extension Spec

## Purpose

A full-stack UI helps users view and control the harness without coupling UI code to the core agent runtime.

## Recommended Structure

```text
apps/web_console/
├── README.md
├── package.json
├── src/
├── tests/
└── API_CONTRACT.md
```

## API Boundary

The UI should call harness APIs such as:

```text
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/skills
GET  /api/evals
POST /api/evals/run
POST /api/external/intake
POST /api/candidates/create
```

## Forbidden Direct Mutations

The UI must not directly write to:

```text
src/harness/safety_gate
specs/harness/promotion_policy.md
skills/*/manifest.yaml
harnesses/pareto_frontier
```

Changes should go through candidates and promotion policy.
