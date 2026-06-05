# Context Compression Policy

## Purpose

Context compression reduces token cost but must preserve debugging precision and safety evidence.

---

## What Can Be Compressed

- long natural language explanations,
- repeated CLI progress output,
- repeated warnings,
- large DOM text blocks,
- old exploratory branches,
- resolved errors.

---

## What Must Be Preserved Exactly

- file paths,
- line numbers,
- command strings,
- exit codes,
- stack trace frames,
- port numbers,
- URLs,
- CSS selectors,
- test names,
- environment variable names,
- security alerts,
- raw evidence references.

---

## Runtime Context Format

```yaml
compressed_observation:
  summary: string
  protected_terms: list[string]
  raw_refs: list[string]
  confidence: float
  compression_method: rule_based | llm | none
```

---

## Compression Safety Rule

If compression would remove or alter protected terms, the compression is invalid.
