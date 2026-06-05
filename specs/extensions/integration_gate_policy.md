# Integration Gate Policy

## Purpose

Every extension must pass gates before stable use.

## Gates

```yaml
required:
  manifest_valid: true
  adapter_registered: true
  unit_tests_pass: true
  integration_eval_pass: true
  safety_review_pass: true
  rollback_defined: true
  budget_declared: true
```

## Human Review Required If

- extension can execute shell commands,
- extension reads private data,
- extension processes camera or microphone input,
- extension introduces network calls,
- extension modifies safety policy,
- extension imports third-party code into `src/`.

## Promotion Levels

```text
experimental
staging
approved
stable
deprecated
```
