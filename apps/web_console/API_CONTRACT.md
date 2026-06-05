# Web Console API Contract

## Read APIs

```text
GET /api/runs
GET /api/runs/{run_id}
GET /api/skills
GET /api/evals
GET /api/external/sources
```

## Write APIs

```text
POST /api/evals/run
POST /api/external/intake
POST /api/candidates/create
```

## Safety Rules

- No direct writes to `skills/` stable packages.
- No direct writes to `specs/harness/promotion_policy.md`.
- No direct execution of shell commands from UI input.
- All write actions produce trace events.
