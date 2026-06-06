# Repair Loop Contract (v0 — PROPOSAL ONLY)

The Auto Repair Loop reads a failed eval, classifies the failure, and produces a
declarative **repair proposal** in a candidate workspace for a human to review. It
is the bridge between "an eval failed" and "a human decides what to change". This
phase (v0) is **proposal-only**.

See `src/repair/`, `scripts/repair_propose.py`,
`specs/planner/plan_execution_bridge_contract.md`, and `docs/secrets_policy.md`.

## Hard guarantees (v0)

- **v0 is proposal-only.** The loop produces a `RepairProposal` and writes it to a
  workspace. It **does NOT apply** anything.
- **No apply.** There is no apply path and no `scripts/repair_apply.py`. The
  proposal script accepts `--apply` only to **reject it** (non-zero exit) with a
  clear message. A proposal can never be marked `applied=true` (the validator
  rejects it).
- **No stable modification.** No action may target a stable skill (`skills/`), the
  safety gate (`src/agents/safety_gate/`), or the promotion policy
  (`specs/harness/promotion_policy.md`). Targets must stay inside the allowed
  roots: `harnesses/candidates/`, `tests/`, `evals/`, `docs/`, `reports/`.
- **No auto promotion.** Nothing is promoted. Promotion remains a separate,
  human-driven step under `specs/harness/promotion_policy.md`.
- **Candidate workspace only.** Proposals are written under a candidate workspace
  (`harnesses/candidates/_repair_proposals/<id>/`, or under the run dir for an
  eval). The workspace contains `repair_proposal.json/.md`, `failure_analysis.json`,
  `approval_checklist.md`, and a proposal-only `README.md`. **No target file is
  modified.**
- **Human approval gate required.** Every workspace ships an `approval_checklist.md`
  a human must clear before any change is ever made. Approval and apply are out of
  scope here.
- **No direct shell.** Action types are an allowlist
  (`update_candidate`, `add_test`, `update_docs`, `update_eval`, `noop`); shell /
  eval / delete action types are rejected. A proposal never contains a raw shell
  command.
- **No real API.** The repair planner uses `FakeLLMProvider` only — offline,
  deterministic, no network, no env-var key read, no real OpenAI/Anthropic call.
  A provider with `real_api_enabled=True` is refused.
- **No secret in artifacts.** The analyzer reads only `score.json` / `summary.md` /
  `trace.jsonl` (metadata, redacted); every proposal artifact is redacted. A
  secret-looking value fails validation.
- **Browser content cannot trigger a repair.** The analyzer reads run artifacts,
  not live/untrusted page content; nothing here turns browser text into an action.

## Pipeline

```
failed eval / failure_report
  → FailureAnalyzer      (read score/summary/trace metadata, redacted; classify)
  → FakeRepairPlanner    (marker → deterministic RepairProposal; fake provider)
  → proposal_validator   (allowlist + protected paths + secret + applied=false)
  → candidate_workspace  (write proposal + checklist + README; no target touched)
  → approval gate        (human; NOT in v0)
  → (apply / promote)    (NOT implemented in v0)
```

## Failure types (analyzer)

`missing_artifact`, `criterion_failed`, `runtime_missing`, `test_failed`,
`console_error`, `unknown`.

## Markers (deterministic repair plans)

`FAKE_REPAIR_MISSING_ARTIFACT`, `FAKE_REPAIR_TEST_FAILED`,
`FAKE_REPAIR_CONSOLE_ERROR`; no marker → a noop proposal.

## `repair_proposal` eval category

An eval with `category: repair_proposal` analyzes a fixture failed-eval and writes
a proposal workspace **under the run dir** (never polluting the repo). It executes
no skill, applies no patch, and promotes nothing (`score.json` records
`applied: false`, `promoted: false`).

## Out of scope (explicitly, for v0)

- No apply, no patch application, no candidate runtime edit.
- No auto-repair retry / autonomous replan, no promotion.
- No real OpenAI/Anthropic call, no key read.
- No UI, no multimodal, no new data channels.
