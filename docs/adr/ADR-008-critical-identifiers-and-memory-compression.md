# ADR-008: Preserve Critical Identifiers During Compression

## Status

Accepted.

## Context

Context compression is necessary for long CLI/browser traces. However, debugging and browser verification depend on precise identifiers.

## Decision

Compression must never remove critical identifiers.

Protected identifiers include:

- file paths,
- line numbers,
- function names,
- stack trace frames,
- exit codes,
- port numbers,
- URLs,
- CSS selectors,
- test names,
- environment variable names,
- command names,
- security alert strings.

## Consequences

- Sensory filtering can summarize long explanations.
- Raw logs must remain available by artifact reference.
- Runtime context should include short summaries plus protected identifiers and raw references.
