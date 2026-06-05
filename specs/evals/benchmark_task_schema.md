# Benchmark Task Schema

```yaml
id: string
category: cli_only | browser_only | cli_browser_integration | adversarial | sharded_multiturn | regression
difficulty: easy | medium | hard

fixture:
  path: string
  reset_command: string | null

user_goal: string

required_skills:
  - string

success_criteria:
  - string

forbidden_actions:
  - string

scoring:
  success_rate: float
  max_steps: integer
  max_runtime_sec: integer
```

## Rules

- Every eval task must be deterministic when possible.
- Every fixture must be resettable.
- Every success criterion must be verifiable.
- Every forbidden action must be trace-detectable.
