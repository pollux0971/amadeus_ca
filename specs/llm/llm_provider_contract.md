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

## Config loading contract

- The provider layer is configured from `config/config.json` (local-only,
  gitignored) or `config/config.example.json` (safe template), validated by
  `scripts/validate_config.py`.
- **The config never contains a key value** — only `llm.api_key_env` (an env var
  NAME). The provider reads the actual key from that environment variable **only
  when real calls are explicitly enabled** (`allow_real_api_calls=true`, provider
  not `fake`, and a key present at run time).
- **Default is the `fake` provider** (`provider=fake`, `enabled=false`,
  `allow_real_api_calls=false`).
- `allow_real_api_calls=true` requires `provider != fake`, a non-null
  `api_key_env`, `redact_secrets=true`, and `fail_closed=true`.
- Loading config performs **no env-var value read and no API call**; only the
  provider's real call path (operator-enabled) ever reads the key, and even then
  it is redacted in all logging/trace per the rules above.

## Current implementation status

- **Implemented: the `fake` provider only** (`src/llm/`): `types.py`, `provider.py`
  (abstract interface), `fake_provider.py` (deterministic, offline, no env reads),
  `redaction.py`, `config_loader.py` (`build_provider`, fail-closed).
- **Real providers (openai / anthropic) are intentionally NOT implemented.** The
  loader fails closed: a real provider with `allow_real_api_calls=false` raises
  `real_api_not_allowed`; even when allowed it raises `real_provider_not_implemented`.
- **No secret in request / response logs** — all logging goes through redaction.
- **The planner (future) must first pass the fake-provider tests** and the fake
  smoke (`scripts/llm_smoke.py --fake-only`, wired into `validate_workflows`).

## Out of scope (explicitly)

- No real OpenAI/Anthropic HTTP call is implemented or enabled.
- No LLM planner, no auto-repair loop. Those are separate, gated phases.
