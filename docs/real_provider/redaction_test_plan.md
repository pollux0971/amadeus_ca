# Real Provider — Redaction Test Plan (planning only)

Planning only — **no real provider implemented, no real API call**. This is the test
plan a future real-provider build story must implement and pass **before** any real
client ships. It proves that no key or sensitive value can reach a trace, log,
report, or commit.

## Goal

For every place a real provider could emit text (request log, response log, usage
metadata, error message), prove `redact_text(emitted) == emitted` — i.e. nothing
secret-looking survives — using only fake/synthetic keys in tests (never a real key).

## Test cases (future)

| # | Test | Asserts |
|---|---|---|
| R1 | request trace redacted | a request carrying a synthetic `sk-…` is logged only as `***REDACTED***` |
| R2 | response trace redacted | a synthetic key / Bearer token in a response body is redacted before logging |
| R3 | usage/metadata redacted | token counts/model id logged; no auth header, no key |
| R4 | error message redacted | a provider exception echoing an `Authorization` header is redacted before it is logged |
| R5 | no key in artifacts | with a synthetic key in the env, no run artifact (`score.json`/`trace.jsonl`/report) contains it |
| R6 | loader reads no key value | source check: no `password_and_api.txt` read; key only via the configured env-var name |
| R7 | fail-closed default | with no key / `allow_real_api_calls=false`, no real call path is reachable; fake is used |
| R8 | smoke stays fake | `scripts/llm_smoke.py --fake-only` still returns the fake provider |

## How keys are simulated

- Tests construct **synthetic** secrets at runtime (e.g. `"sk-" + "x"*40`) so no
  real key and no key-like literal lives in the test source (mirrors the existing
  `test_llm_*` tests).
- Tests set a fake key in `os.environ` for a subprocess/call and assert it never
  appears in stdout/stderr/artifacts.

## Tooling reused

- `src/llm/redaction.py` (`redact_text`, `redact_mapping`) — the redaction under test.
- `scripts/check_secret_hygiene.py` — guarantees no secret is committed.
- `scripts/validate_config.py` — guarantees config holds an env-var name only.

## Exit / pre-build gate

The real-provider build story may proceed only when R1–R8 are implemented and pass,
the loader still defaults to fake and fails closed, and an operator opt-in is
required for any real call. **This planning story implements none of these tests
against a real client and makes no real API call.**
