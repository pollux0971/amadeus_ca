# Extension Adapter Spec

## Purpose

Extensions must not directly couple to the orchestrator. They integrate through adapters.

## Adapter Interface

```python
class ExtensionAdapter:
    extension_id: str
    category: str
    risk_level: str

    def validate_config(self) -> list[str]: ...
    def describe_capabilities(self) -> dict: ...
    def estimate_cost(self, request: dict) -> dict: ...
    def run(self, request: dict) -> dict: ...
```

## Categories

```text
interface
data_channel
multimodal_processor
tool_provider
skill_provider
eval_provider
report_provider
```

## Runtime Requirements

Adapters must:

- return structured output,
- emit trace events,
- declare budget impact,
- declare trust level,
- provide a disable switch,
- avoid direct mutation of stable files.
