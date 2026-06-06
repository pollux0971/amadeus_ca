# Real Provider — Threat Model (planning only)

Planning only — **no real provider implemented, no real API call**. This enumerates
the threats a future real LLM provider introduces and the mitigation each maps to.
The bar: a real provider may be built only after every mitigation here is
implemented and tested.

## Assets to protect

- **API keys** (OpenAI / Anthropic) — never committed, never logged, never rendered.
- **Prompt / response content** — may contain user data; must be redacted in trace.
- **The fail-closed default** — the harness must never silently start calling a real
  API.

## Threats and mitigations

| # | Threat | Vector | Mitigation (required before build) |
|---|---|---|---|
| T1 | Key leaks into a commit/trace/report | logging request/response or config dump | redact all trace (`src/llm/redaction.py`); config holds env-var **name** only; secret hygiene scanner stays green |
| T2 | Key read from the wrong place | reading `.env` values or `password_and_api.txt` | keys read **only** from the named env var at call time; never read `.env`/password file; see `env_var_loading_policy.md` |
| T3 | Real calls happen unintentionally | default config drift; code path reachable without opt-in | fail-closed loader: provider=fake default; real requires `allow_real_api_calls=true` + provider != fake + key present; operator opt-in only |
| T4 | Untrusted content triggers a real call | browser/page/file content turned into a prompt that calls out | untrusted content is never a control signal (ADR-003); a real call is only ever initiated by an explicit, vetted code path |
| T5 | Prompt/response data exfiltration | sending sensitive repo/secret content to a third party | redact before send where applicable; never include secrets in prompts; document data-egress in the build story |
| T6 | Cost / abuse (runaway calls) | loops calling a paid API | rate/iteration caps + explicit opt-in; fake provider used for all tests/CI |
| T7 | Supply-chain / SDK risk | malicious or vulnerable provider SDK | pin + review the SDK in the build story; no SDK added in this planning story |
| T8 | Error messages leak keys | provider SDK exceptions echoing auth headers | wrap provider errors through redaction before logging |

## Trust boundaries

- **Inside (trusted):** the harness code paths that explicitly construct a real
  provider after the operator opt-in.
- **Outside (untrusted):** browser/page/file content, eval fixtures, anything that
  could influence a prompt — never allowed to *initiate* a real call.

## Pre-build acceptance bar (future)

A real provider build story may proceed only when:
- the env-var loading policy is implemented exactly as in
  [`env_var_loading_policy.md`](env_var_loading_policy.md),
- the redaction test plan in [`redaction_test_plan.md`](redaction_test_plan.md) is
  implemented and passing,
- the loader still defaults to fake and fails closed,
- and an operator explicitly opts in for any real call.

**No real API call, no provider client, and no key read are part of this planning
story.**
