# Extension Adapter Template

## Adapter ID

`example_adapter`

## Purpose

Describe the external feature or source this adapter connects to the harness.

## Input Schema

```yaml
input:
  field_name:
    type: string
    required: true
```

## Output Schema

```yaml
output:
  artifact_refs:
    type: list
  summary:
    type: string
```

## Permissions

```yaml
permissions:
  filesystem_read: true
  filesystem_write: false
  shell_execution: false
  browser_access: false
  network_access: false
  secret_access: false
```

## Safety Notes

- What could go wrong?
- What must be blocked?
- What data must not enter prompt context?

## Tests

- schema validation
- adapter health check
- permission boundary test
- budget test
- regression test
