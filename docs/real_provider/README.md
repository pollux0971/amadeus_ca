# Real LLM Provider — Planning (story_real_provider_v0)

> **STATUS UPDATE — Real Provider Implementation v0 has SHIPPED.** The planning gate
> below has been satisfied: `src/llm/openai_provider.py` and
> `src/llm/anthropic_provider.py` now exist (minimal, stdlib `urllib`). The **fake
> provider remains the default**, the loader is **fail-closed**, the key is read only
> from the named env var at call time, every artifact is redacted, and there is **no
> real API call by default** (operator opt-in via `scripts/llm_provider_smoke.py
> --real-call` with `allow_real_api_calls=true` + the env var set). See
> `specs/llm/llm_provider_contract.md` and the planning docs in this folder for the
> safety requirements the implementation meets.

> **FOLLOW-UP — Real Provider Planner Integration v0 has SHIPPED.** The real
> provider is now reachable through the planner via `src/planner/provider_planner.py`
> (`ProviderBackedPlanner` + `build_planner_from_config`). It stays **fail-closed and
> plan-only**: the **fake provider is still the default**, a real provider is built
> only under config opt-in (`provider != fake` + `allow_real_api_calls=true` +
> `api_key_env`), and in a dry-run the real provider is **HELD but never called** —
> the plan is built deterministically from the marker. There is **no real API call**
> and **no real-call path** in `scripts/planner_provider_smoke.py`; the planner still
> never executes a step. See `specs/llm/llm_provider_contract.md` →
> "Planner provider use (current)".

**Original planning status:** planning gate only — **no real provider implemented, no
real API call**. This folder is the deliverable of
[`../epics/stories/story_real_provider_v0.md`](../epics/stories/story_real_provider_v0.md)
under [`EPIC-PROVIDER`](../epics/epic_real_provider.md).

A future real provider (OpenAI / Anthropic) would sit behind the existing
fail-closed interface in `src/llm/` so the harness *could* use a real model when an
operator explicitly opts in. This story only **plans** it; it implements no client
and calls no API. The **fake provider remains the default**.

## Hard boundaries (carried from the epic)

- **No real API call.** Fake provider is the default; the loader fails closed.
- **Never read `/data/python/computer_agent_v5/password_and_api.txt`** or `.env` key
  *values* during planning.
- **No key in config** — config references an env var **name** only (e.g.
  `OPENAI_API_KEY`), never a key value.
- **Keys read only from the named env var**, and only when real calls are explicitly
  enabled (`allow_real_api_calls=true`, provider != fake, key present at run time).
- **Operator opt-in only.** Nothing enables real calls automatically.
- **All request/response trace MUST be redacted** (`src/llm/redaction.py`).
- **Fail closed:** no key or not approved → do not call a real API (fall back to
  fake or block with a clear reason).

## Planning documents

- [`threat_model.md`](threat_model.md) — egress, key handling, leak paths, abuse
  cases, and the mitigation each maps to.
- [`env_var_loading_policy.md`](env_var_loading_policy.md) — exactly how a key is
  loaded (named env var only, gated, never config/file).
- [`redaction_test_plan.md`](redaction_test_plan.md) — how request/response trace is
  proven redacted **before** any real client is ever added.

## Relationship to existing contracts

This planning set refines, and does not change,
[`../../specs/llm/llm_provider_contract.md`](../../specs/llm/llm_provider_contract.md)
and [`../secrets_policy.md`](../secrets_policy.md). The current `src/llm/` fake
provider + `config_loader` already fail closed; this story specifies what a real
provider must satisfy before it could be added in a separate, gated build story.

## Out of scope (this story)

- Any OpenAI/Anthropic client code or HTTP call.
- Any change that makes real calls reachable by default.
- UI / stable-promotion / multimodal work (separate epics).
