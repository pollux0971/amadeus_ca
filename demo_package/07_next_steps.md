# 07 — Next Steps

The forward backlog, from [`../docs/epics/decision_matrix.md`](../docs/epics/decision_matrix.md).
**One bounded story per `/goal` run; no auto-extension.** Each option keeps every
boundary in [`06_safety_boundaries.md`](06_safety_boundaries.md).

## Options

| Option | Status | Risk | What it needs before it can proceed |
|---|---|---|---|
| **Stable Promotion** | **BLOCKED / high risk** | Highest — the only step that changes what runs by default | human review of a staging workspace + verified rollback + full regression + human shell-execution review + promotion policy + explicit operator approval |
| **UI** | read-only **complete** (skeleton + smoke gate) | Low | a future **action UI** would require new gates: every action routes through existing approval-gated scripts; no promote-from-UI; new evals for any write path |
| **Real Provider** | **planning only** | High (egress + key handling) | implement env-var-name-only loading + redaction tests (R1–R8); **operator opt-in**; fake stays default; fail closed; no `password_and_api.txt` |
| **Multimodal / Data Channels** | **planning only** | High (new untrusted surface) | per-channel **source isolation** + untrusted-content policy + its own eval (incl. adversarial fixtures) before any runtime channel |

## Recommended ordering

1. Lowest-risk, highest-clarity: a further **read-only** UI increment, or wiring an
   existing planning epic toward a build story by **first** adding its evals.
2. **Real Provider** and **Multimodal** remain planning-gated until their threat
   model / isolation evals exist and pass.
3. **Stable Promotion** stays blocked until a human is ready to clear all its gates;
   a story may produce the review package and otherwise mark itself **blocked**.

## Rule

Pick **one** story from the decision matrix, work inside its Scope / Acceptance
Criteria / Forbidden Zone, finish with a checkpoint or report, then **stop**. Do not
start the next story automatically.
