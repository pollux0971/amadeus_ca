# 10 — Future Work

From the backlog [`../docs/epics/decision_matrix.md`](../docs/epics/decision_matrix.md).
**One bounded story per `/goal` run.** Each option keeps every safety boundary in
[`07_safety_and_risk_management.md`](07_safety_and_risk_management.md).

## 1. Stable Promotion — human review (BLOCKED / highest risk)

The stable-promotion readiness audit recommends **NO-GO / BLOCKED**. Before any GO, a
human must complete:

- human shell-execution review sign-off,
- promotion-policy review sign-off,
- explicit operator approval,
- deployed-state rollback verification review,
- a full-regression attestation.

Only then may a separate, gated stable-promotion story execute under
`specs/harness/promotion_policy.md` with a captured approval marker + verified
rollback. See `reports/stable_promotion_readiness_audit_v0/05_required_human_review.md`.

## 2. UI action gates (read-only complete)

The dashboard is read-only (skeleton + smoke gate done). A future **action UI** would
require new gates: every action routes through existing approval-gated scripts; no
promote/apply/merge/stage from the UI; new evals for any write path.

## 3. Real Provider — gated implementation (planning only)

Implement a real OpenAI/Anthropic provider behind the fail-closed interface, but only
after: env-var-name-only key loading, the redaction test plan (R1–R8), **operator
opt-in**, fake stays default, fail closed, and never reading `password_and_api.txt`.
See `docs/real_provider/`.

## 4. Multimodal / Data Channels (planning only)

Add file/image/PDF/web channels, but only with per-channel **source isolation**, an
untrusted-content policy (content is data, never an instruction), and each channel's
own eval (incl. adversarial fixtures) before any runtime. See
`docs/multimodal_data_channels/`.

## Sequencing

Lowest-risk first (further read-only increments, or wiring a planning epic toward a
build story by adding its evals first). Real provider and multimodal stay
planning-gated; stable promotion stays blocked until its human gates are cleared.
