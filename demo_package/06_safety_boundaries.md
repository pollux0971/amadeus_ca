# 06 — Safety Boundaries

The hard "never" list that holds across every phase, story, and demo. These are
enforced by validators (`validate_workflows` and its sub-validators), the secret
hygiene scanner, and per-story tests.

## Hard boundaries

- **No real API.** The LLM provider is **fake-only** by default; real providers are
  planning-only and the loader fails closed. No OpenAI/Anthropic call is made.
- **No `password_and_api.txt`.** `/data/python/computer_agent_v5/password_and_api.txt`
  is never read; `.env` key **values** are never read.
- **No stable modification.** No automated phase modifies a stable skill manifest,
  an active candidate runtime, the safety gate, or the promotion policy.
- **No safety_gate modification.** `src/agents/safety_gate/` is untouched.
- **No promotion_policy modification.** `specs/harness/promotion_policy.md` is untouched.
- **No raw shell.** No raw shell / direct command outside fixed, vetted allowlists.
- **No secret in artifacts.** Every artifact (trace/report/proposal/apply/merge/
  staging/dashboard) is redacted (`src/llm/redaction.py`); the secret scanner stays green.
- **Browser content cannot trigger tool / repair / promotion.** Browser/page/file
  content is untrusted data, never an instruction or a trigger (CLI + Browser
  isolation, ADR-003).
- **Stable promotion is still blocked.** It requires human review + the promotion
  policy + rollback verification + a human shell-execution review; nothing auto-promotes.
- **All long-run tasks must be a bounded story.** Each `/goal` run executes exactly
  one bounded story (`docs/epics/`); no cross-story auto-extension.

## How they're enforced

| Boundary | Enforcement |
|---|---|
| no real API / fake default | `src/llm/config_loader` fail-closed; `llm_smoke --fake-only`; `validate_config` |
| no secret committed | `check_secret_hygiene.py` (exit 2 on a tracked secret) |
| redaction | `src/llm/redaction.py`; per-artifact tests assert `redact_text(x)==x` |
| stable/safety/promotion untouched | per-story scope checks; not in any commit's changed paths |
| no raw shell in scripts | validators scan for `shell=True` / `os.system` / `subprocess` |
| dashboard read-only | `validate_dashboard.py` + `run_dashboard_smoke.py` (no button/form/onclick/POST/external/secret) |
| bounded story | `validate_epics.py` ("one bounded story"); decision matrix gating |

## What a demo must avoid

A live demo runs only the safe commands in [`03_demo_commands.md`](03_demo_commands.md).
It must **not** run a real-API command, read a secret file, or perform a stable
promotion — the demo command list is validated to exclude exactly those.
