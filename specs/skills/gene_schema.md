# Gene Schema

Gene 是 runtime context 中使用的短控制表示。  
目標是取代把整份 SKILL.md 塞進 prompt。

```yaml
id: string
keywords:
  - string
summary: string
strategy:
  - string
avoid:
  - string
validation:
  - string
constraints:
  - string
```

## Rules

- Gene should be short.
- Gene should contain failure-aware `avoid` cues.
- Gene should include validation hooks.
- Gene should not include long examples.
- Gene should not include secrets.
