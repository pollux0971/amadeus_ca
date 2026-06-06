# Real Provider — Env Var Loading Policy (planning only)

Planning only — **no real provider implemented, no key read**. This specifies
exactly how a future real provider would obtain an API key. The rule is narrow on
purpose: a key may be read **only** from a named environment variable, **only** at
call time, **only** when real calls are explicitly enabled.

## The only allowed key source

- Config stores an **env var name** (e.g. `"api_key_env": "OPENAI_API_KEY"`), never
  a key value.
- At call time, and only then, the provider reads `os.environ[<api_key_env>]`.
- If the named env var is absent → **fail closed** (fall back to fake or block with
  `failure_reason=llm_provider_unavailable`); never improvise.

## Forbidden key sources

- **`.env` key *values*** — never read by planning or by the loader; `.env` is for
  the operator's own shell, not for the harness to parse for values.
- **`/data/python/computer_agent_v5/password_and_api.txt`** — never read, ever.
- **`config/config.json` / `config.example.json`** — may hold the env var **name**
  only; a key value there is a hard error (secret hygiene + `validate_config`).
- **Browser/page/file content** — never a key source.
- **Command-line args / CLI flags** — no key passed as an argument (would land in
  process listings / history).

## Gating (operator opt-in, fail closed)

A real call is reachable only when ALL hold (already encoded by `config_loader`):

1. `provider != "fake"`,
2. `allow_real_api_calls == true`,
3. `redact_secrets == true` and `fail_closed == true`,
4. the named env var is present at run time.

Miss any → no real call. Default config is `provider=fake`, `enabled=false`,
`allow_real_api_calls=false` — so the out-of-the-box behavior is fake + fail closed.

## Handling rules

- The key value is held only in a local variable for the duration of a call; it is
  never stored, logged, written to disk, or placed in a trace/report.
- Every trace/report goes through `src/llm/redaction.py`; a key pattern that somehow
  reaches a log becomes `***REDACTED***`.
- Provider construction and config loading perform **no env-var value read**; only
  the (future) real call path reads the key, and only under the gating above.

## Verification (future build story)

- A unit test asserts the loader/config code contains **no** `password_and_api.txt`
  read and reads the key **only** via the configured env-var name.
- `scripts/check_secret_hygiene.py` and `scripts/validate_config.py` stay green (no
  key value anywhere in tracked files / config).

**This planning story reads no key and makes no real call.**
