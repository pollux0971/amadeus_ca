# LLM Provider Contract (spec only — no real API implementation)

A minimal specification for a future LLM provider layer. **This is a spec, not an
implementation.** No real API call exists or is enabled by this document. It
exists so that a later LLM-planner / auto-repair phase has a secure, fail-closed
contract to build against. See `docs/secrets_policy.md` and ADR-013.

## Provider interface

A provider exposes a single capability (shape, not code):

```
complete(request) -> response
  request:  { prompt | messages, model, max_tokens, ... }   # no secrets in here
  response: { text, usage, provider, model, redacted: bool }
```

Selection is via `LLM_PROVIDER` (default **`fake`**). Keys come ONLY from the
environment / a local `.env` (never from the repo, never from browser content).

### fake provider (default)

- Returns deterministic, canned/echo output. **Requires no key.**
- Used by default and as the fail-closed fallback. Safe in CI and offline.

### openai provider

- Would call the OpenAI API using `OPENAI_API_KEY` from the environment.
- **Not implemented / not enabled here.** Requires explicit operator opt-in
  (`LLM_PROVIDER=openai` with a key present).

### anthropic provider

- Would call the Anthropic API using `ANTHROPIC_API_KEY` from the environment.
- **Not implemented / not enabled here.** Requires explicit operator opt-in
  (`LLM_PROVIDER=anthropic` with a key present).

## Redaction policy

- Every provider MUST redact secrets (API keys, `Authorization` headers,
  key-like tokens) to `***REDACTED***` before any value is logged, traced,
  returned in a report, or placed into a prompt echoed back.
- Redaction applies to request metadata, error messages, and response logging.

## No-secret-in-trace rule

- Provider activity written to `runs/` / `trace.jsonl` / `score.json` / reports
  MUST contain no key material — only provider name, model id, token counts, and
  redacted metadata.

## Fail-closed behavior

- **No key available → do NOT call a real API.** The layer either:
  - falls back to the `fake` provider (default), or
  - returns a blocked result with `failure_reason=llm_provider_unavailable`.
- An unknown/misconfigured provider is treated as `fake` or blocked — never an
  excuse to proceed without a key.
- Browser/untrusted content can never select a real provider or supply a key.

## Out of scope (explicitly)

- No real OpenAI/Anthropic HTTP call is implemented or enabled.
- No LLM planner, no auto-repair loop. Those are separate, gated phases.
