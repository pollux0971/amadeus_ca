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

> **FOLLOW-UP — OpenAI Real Provider Live Smoke v0 has SHIPPED (OpenAI only).**
> `scripts/real_provider_live_smoke.py` + `tests/unit/test_real_provider_live_smoke_script.py`
> now exist. It is **dry-run by default** (verifies config / env-var NAME / provider
> construction / redaction with **no network call**); a real call needs explicit
> operator opt-in (`--real-call`) **and** the named env var present at run time, else
> it **fails closed (exit 2 = BLOCKED)**. The prompt is **FIXED**
> (`Reply with exactly: provider-ok`, never arbitrary); `max_tokens` is a small safe
> default so the smoke never produces long output. The key is read **only from
> `OPENAI_API_KEY` at call time** — never from a file, `.env`, `config`, or
> `password_and_api.txt` — and is never printed, traced, or written to a report.
> All stdout/stderr and the `live_smoke_report.json` / `live_smoke_report.md`
> artifacts (written under the gitignored `runs/real_provider_live_smoke/` by
> default) are **redacted**. **Anthropic is intentionally BLOCKED / NOT TESTED this
> round** — `--provider anthropic --real-call` returns exit 2. This script runs **no
> planner, no plan execution, no auto-repair, and no stable promotion**. It is wired
> into `scripts/validate_workflows.py` as a real-provider live-smoke safety check
> (dry-run only — the gate makes no real API call). Commands:
>
> ```bash
> python scripts/real_provider_live_smoke.py --provider openai --dry-run            # safe anywhere
> python scripts/real_provider_live_smoke.py --provider openai --real-call --expect provider-ok  # operator opt-in; needs OPENAI_API_KEY
> ```

> **FOLLOW-UP — OpenAI Planner Live Plan-Only v0 has SHIPPED (OpenAI only).**
> `scripts/openai_planner_live_plan.py` + `src/planner/provider_planner.py`
> (`ProviderBackedPlanner.live_plan` + `parse_plan_from_text` + `LivePlanError`) let
> the OpenAI provider generate **one real planner plan** — strictly **plan-only**
> (never executed, never auto-repaired, no repair/apply/merge/staging/promotion). It
> is **dry-run by default** (config / provider / redaction / schema check, **no API
> call**); a real call needs `--real-call` **+** provider=openai **+**
> `allow_real_api_calls=true` **+** `OPENAI_API_KEY` present, else it **fails closed**.
> Only a **FIXED system prompt + the goal** are sent — never file content, browser/page
> content, or raw run traces — and a secret-looking goal is refused. The generated
> plan MUST pass `PlanValidator`; a non-JSON response or an invalid plan produces a
> **blocked report** (no auto-fix). On success it writes redacted `plan.json`,
> `plan_summary.md`, and `planner_live_report.json` (under the gitignored
> `runs/openai_planner_live_plan/`). The key is read **only from
> `os.environ['OPENAI_API_KEY']` at call time** and is never printed/traced/committed;
> config holds the env-var NAME only. Wired into `scripts/validate_workflows.py` as a
> live-planner safety check (dry-run only — no real API call in the gate). Commands:
>
> ```bash
> python scripts/openai_planner_live_plan.py --goal "Create a safe read-only project status inspection plan. Do not execute anything." --dry-run   # safe anywhere
> python scripts/openai_planner_live_plan.py --goal "Create a safe read-only project status inspection plan. Do not execute anything." --real-call  # operator opt-in; needs OPENAI_API_KEY
> ```

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
