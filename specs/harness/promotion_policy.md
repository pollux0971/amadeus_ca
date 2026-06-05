# Promotion Policy

## Levels

### dev

Experimental candidate. May fail.

### staging

Candidate passed required tests but still needs broader observation.

### stable

Approved for main demo and baseline comparison.

---

## Required Checks

```yaml
required:
  unit_tests_pass: true
  integration_tests_pass: true
  security_tests_pass: true
  no_secret_leak: true
  no_destructive_command: true
```

---

## Metric Gates

```yaml
metrics:
  success_rate_delta_min: 0.00
  regression_tolerance: 0.00
  runtime_increase_max: 0.20
  token_cost_increase_max: 0.20
  flaky_rate_max: 0.05
```

---

## Human Review Required If

- modifies shell execution
- modifies safety gate
- reads `.env`
- deletes files
- installs packages
- modifies promotion policy
- modifies secret scanner
- changes browser-to-cli trust rules

---

## Promotion Decision

```yaml
decision:
  candidate_id: string
  promote_to: reject | dev | staging | stable
  reason: string
  required_followup:
    - string
```
