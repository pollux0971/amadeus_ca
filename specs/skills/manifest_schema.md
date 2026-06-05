# Manifest Schema

```yaml
id: string
version: string
level: planning | functional | atomic
domain:
  - cli
  - browser
  - browser_bridge
  - safety
  - verifier
status: draft | tested | staging | stable | deprecated

entrypoint:
  type: python | markdown | external | none
  path: string | null

inputs:
  input_name:
    type: string | integer | boolean | object | array
    required: boolean
    default: any

outputs:
  output_name:
    type: string | integer | boolean | object | array

permissions:
  filesystem:
    read: boolean
    write: boolean
  shell:
    run_command: boolean
    allow_network: boolean
  browser:
    required: boolean

risk_level: low | medium | high

preconditions:
  - string

postconditions:
  - string

tests:
  unit:
    - string
  eval:
    - string
```
