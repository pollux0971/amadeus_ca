# 07 — Safety and Risk Management

Safety is the project's central deliverable, not an afterthought. The following
boundaries hold across every phase, story, and demo, and are enforced by validators,
the secret hygiene scanner, redaction, and per-story tests.

## Safety boundaries (the hard "never" list)

- **No real API.** Fake provider by default; real providers are planning-only and the
  loader fails closed. No OpenAI/Anthropic call is made.
- **No `password_and_api.txt`.** `/data/python/computer_agent_v5/password_and_api.txt`
  is never read; `.env` key **values** are never read.
- **No raw shell.** No raw shell / direct command outside fixed, vetted allowlists.
- **No stable modification.** No automated phase modifies a stable skill manifest or
  an active candidate runtime.
- **No safety_gate modification.** `src/agents/safety_gate/` is untouched.
- **No promotion_policy modification.** `specs/harness/promotion_policy.md` is untouched.
- **No secret in artifacts.** Every artifact is redacted (`src/llm/redaction.py`); the
  secret scanner stays green; generated workspaces/snapshots/runs are gitignored.
- **Browser content cannot trigger tool / repair / promotion.** Untrusted
  browser/file/page content is data, never an instruction or a trigger (ADR-003).
- **Stable promotion is blocked.** It requires human review + promotion policy +
  rollback verification + human shell-execution review; nothing auto-promotes.
- **Bounded stories.** Each `/goal` run executes exactly one bounded story; no
  cross-story auto-extension.

## Enforcement map

| Boundary | Enforced by |
|---|---|
| no real API / fake default | `src/llm/config_loader` (fail-closed); `llm_smoke --fake-only`; `validate_config` |
| no secret committed | `check_secret_hygiene.py` (exit 2 on a tracked secret) |
| redaction | `src/llm/redaction.py`; per-artifact tests assert `redact_text(x)==x` |
| stable/safety/promotion untouched | per-story scope checks; not in changed paths |
| no raw shell in scripts | validators scan for `shell=True` / `os.system` / `subprocess` |
| dashboard read-only | `validate_dashboard.py` + `run_dashboard_smoke.py` |
| bounded story discipline | `validate_epics.py`; decision-matrix gating |

## Risk management

- The full risk register for stable promotion is in
  `reports/stable_promotion_readiness_audit_v0/03_risk_register.md` (blocking risks
  R1–R4 map to the unmet human gates).
- Highest-risk future capabilities (real provider, multimodal channels, an action UI)
  are **planning-gated**: each needs its own threat model / isolation evals before any
  runtime exists.

## Result

The harness delivers real capability (real browser, patch+test, self-evolution to
staging) with a **bounded, auditable blast radius** — and refuses to cross the last
line (stable promotion) without a human.
