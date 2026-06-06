# Story PROVIDER-V0 — Real provider planning gate only

**Epic:** EPIC-PROVIDER
**Status:** ready (planning only)

## Goal

Plan a future real LLM provider (OpenAI / Anthropic) behind the existing
fail-closed interface — **planning only**, no real provider implemented and no real
API call.

## Scope

- Write the provider **threat model** (egress, key handling, prompt/response leak
  paths, abuse cases).
- Write the **env-var loading policy** (key read only from a named env var, only
  when explicitly enabled; never from config or a file).
- Write the **redaction test plan** (how request/response trace is proven redacted
  before any real client is ever added).

## Out of Scope

- Any OpenAI/Anthropic client code or HTTP call.
- Any change that makes real calls reachable by default.

## Preconditions

- `src/llm/` fake provider + config contract exist
  (`specs/llm/llm_provider_contract.md`, `docs/secrets_policy.md`).

## Implementation Boundaries

- May write only planning docs (under `docs/` and/or `specs/llm/`).
- May **not** add a provider client, enable real calls, or read any key value.

## Acceptance Criteria

- [ ] provider threat model written
- [ ] env var loading policy written (named env var only; never config/file)
- [ ] redaction test plan written
- [ ] no real API call
- [ ] no provider client implemented
- [ ] fake provider remains default (loader still fails closed)

## Forbidden Zone

- **No real API call.** **No provider client** in v0.
- **Never read `/data/python/computer_agent_v5/password_and_api.txt`** or `.env`
  key values.
- **No key in config** (env var **name** only). Real API is operator opt-in only.
- All request/response trace must be redacted. Fake provider stays the default.

## Required Validation Commands

```bash
python scripts/validate_structure.py
python scripts/validate_workflows.py
python scripts/check_secret_hygiene.py
python scripts/validate_config.py
python scripts/llm_smoke.py --fake-only
python scripts/run_unit_tests.py
```

## Artifacts to Produce

- Planning docs: threat model, env-var loading policy, redaction test plan (all
  redacted; no secret; no key material).

## Rollback / Stop Condition

- **Rollback:** delete the planning docs — nothing runtime changed; fake provider
  still default.
- **Stop Condition:** stop when the Definition of Done is met; do not implement any
  provider client or continue into another story.

## Definition of Done

Acceptance criteria met; validation green (incl. `llm_smoke --fake-only`); planning
docs exist; fake provider still default; working tree clean; **stop**.
