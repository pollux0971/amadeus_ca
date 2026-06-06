# EPIC-PROVIDER — Real LLM Provider (planning only)

**Status:** planning only — no real provider implemented in this epic's v0 story.
**Depends on:** `src/llm/` fake provider + the config contract
(`specs/llm/llm_provider_contract.md`, `docs/secrets_policy.md`).

## Goal

Plan a future real LLM provider (OpenAI / Anthropic) behind the existing
fail-closed interface, so the harness *could* use a real model when an operator
explicitly opts in. **This epic's current scope is planning only**; no real
provider is implemented and no real API is called.

## Why planning / fail-closed first

A real provider introduces network egress and key handling — the highest-risk
change for secret leakage. The threat model, env-var loading policy, and redaction
test plan must be written and reviewed before any client code exists.

## Hard rules (must be written into every story under this epic)

- **No real API call** in v0 (or by default ever); the **fake provider remains the
  default** and the loader fails closed.
- **Never read `/data/python/computer_agent_v5/password_and_api.txt`** and never
  read `.env` key *values* during planning.
- **No key in config** — config may reference an env var **name** only (e.g.
  `OPENAI_API_KEY`), never a key value.
- **Keys are read only from the named env var**, and only when real calls are
  explicitly enabled (`allow_real_api_calls=true`, provider != fake, key present).
- **Real API requires operator opt-in.** Nothing enables real calls automatically.
- **All request/response trace MUST be redacted** (`src/llm/redaction.py`); no key
  material in `runs/` / `trace.jsonl` / reports.
- **Fail closed:** no key or not approved → do not call a real API (fall back to
  fake or block with a clear reason).

## Stories

- [`stories/story_real_provider_v0.md`](stories/story_real_provider_v0.md) — real
  provider **planning gate only**: threat model, env-var loading policy, redaction
  test plan. No real API call, no provider client, fake provider stays default.

## Out of scope (for this epic, until a later gated story)

- Any OpenAI/Anthropic client code or HTTP call.
- Any change that makes real calls reachable by default.
- UI / stable-promotion / multimodal work (separate epics).
