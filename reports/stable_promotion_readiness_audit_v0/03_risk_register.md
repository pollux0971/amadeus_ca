# 03 — Risk Register

Risks relevant to a stable promotion. Severity: High / Medium / Low. Every
"promotion" risk is currently mitigated by the fact that **stable promotion is
blocked** (no automated path exists).

| ID | Risk | Severity | Status / mitigation |
|---|---|---|---|
| R1 | Promoting a shell-executing candidate (patch runner / server) to stable without a human shell-execution review | **High** | **Open (blocking)** — no human sign-off; promotion blocked |
| R2 | Promotion bypassing `specs/harness/promotion_policy.md` | **High** | **Open (blocking)** — no policy review sign-off; promotion blocked |
| R3 | No verified deployed-state rollback for a stable cut | **High** | **Open (blocking)** — only workspace-level rollback exists; needs human-reviewed rollback |
| R4 | Promotion triggered without explicit operator approval | **High** | **Open (blocking)** — no approval marker captured; promotion blocked |
| R5 | Real-browser gates depend on Playwright/Chromium (.venv) | Medium | Mitigated — `--dry-run` safe; real gates run in .venv; http_fallback is not a real browser |
| R6 | Fake provider only; no real model reasoning validated | Medium | Accepted for now — fake default, fail closed; real provider is a separate planning-gated story |
| R7 | Deterministic fake repair chain (markers, not semantic) | Medium | Accepted — chain proves the *gating*, not real fixes; documented |
| R8 | Secret leakage into artifacts | Low | Mitigated — redaction + secret hygiene scanner green; nothing committed |
| R9 | UI dashboard expanding into an action surface | Low | Mitigated — read-only; smoke gate asserts no button/form/onclick/POST/external/secret |
| R10 | Untrusted (browser/file) content becoming an instruction | Low | Mitigated — CLI + Browser isolation (ADR-003); never a tool/repair/promotion trigger |

## Blocking risks

R1–R4 are **blocking** and map directly to the unmet human gates in
[`02_gate_results.md`](02_gate_results.md). They cannot be cleared by automation; they
require the human steps in [`05_required_human_review.md`](05_required_human_review.md).
