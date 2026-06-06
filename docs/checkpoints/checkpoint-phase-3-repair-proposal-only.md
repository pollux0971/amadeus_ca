# Checkpoint: Phase 3 — Auto Repair Loop v0 (Proposal Only)

- **checkpoint name:** `checkpoint-phase-3-repair-proposal-only`
- **commit (repair v0 passed):** `b1ffd56`
- **tag:** `checkpoint-phase-3-repair-proposal-only`

Frozen snapshot of the chain **failed eval → failure analysis → fake repair
proposal → candidate workspace draft → human approval gate**. Documentation only —
no runtime, candidate, stable skill, safety gate, or promotion policy change.

## What is frozen

- **Repair Loop v0 exists.** `src/repair/` reads a failed eval and produces a
  declarative repair *proposal* in a candidate workspace for human review.
- **Proposal-only.** The loop produces a `RepairProposal`; it **does not apply**
  anything, run a test, or edit candidate/stable code.
- **No apply / no `repair_apply.py`.** There is no apply path and no
  `scripts/repair_apply.py`. `repair_propose.py --apply` is **rejected**
  (non-zero exit). A proposal can never be marked `applied=true` (the validator
  rejects it).
- **No auto promotion.** Nothing is promoted; promotion stays a separate,
  human-driven step under `specs/harness/promotion_policy.md`.
- **Failure analyzer reads only redacted artifact metadata.** It opens only
  `score.json`, `summary.md`, and `trace.jsonl`, redacts everything it keeps, and
  reads no `.env`, password file, or secret.
- **Fake repair planner only.** `FakeRepairPlanner` uses `FakeLLMProvider`
  (offline, deterministic); no network, no env-var key read, no real API call; a
  provider with `real_api_enabled=True` is refused.
- **Proposal validator blocks unsafe proposals.** It rejects targets under
  `skills/`, `src/agents/safety_gate/`, `specs/harness/promotion_policy.md`,
  `.env`, `config/config.json`; rejects `modify_stable_skill` /
  `modify_safety_gate` / `modify_promotion_policy` / `raw_shell` /
  `direct_command` / `delete_file`; requires approval for high-risk; fails on
  secret-looking content; and **rejects `applied=true`**.
- **Candidate workspace created.** Each proposal writes
  `repair_proposal.json` / `repair_proposal.md` / `failure_analysis.json` /
  `approval_checklist.md` / `README.md` — **no target file is modified**.

## Results (frozen)

| Eval / check | Result |
|---|---|
| `fake_repair_proposal_only` (category `repair_proposal`) | **score 1.0** (8/8 criteria) |
| `repair_propose.py --apply` | **rejected** (exit 3, clear message) |
| `scripts/repair_apply.py` | **does not exist** |
| no stable files modified | **true** (targets in allowed roots only) |
| no secret in proposal artifacts | **true** (all redacted) |
| `fake_full_browser_plan_execution` | **still 1.0** (real browser via the gate) |
| `full_browser_vite_login_bug_e2e` | **still 1.0** |

- **secret hygiene: PASS.** **unit tests: 273/273.**

## Pipeline

```
failed eval / failure_report
  → FailureAnalyzer      (read score/summary/trace metadata, redacted; classify)
  → FakeRepairPlanner    (marker → deterministic RepairProposal; fake provider)
  → ProposalValidator    (allowlist + protected paths + secret + applied=false)
  → CandidateWorkspace   (write proposal + checklist + README; no target touched)
  → Human Approval Gate  (a human clears approval_checklist.md — NOT in v0)
  → apply / promote      (NOT implemented in v0)
```

## Frozen constraints

- **stable skills / safety_gate / promotion_policy untouched** throughout.
- No `scripts/repair_apply.py`; no proposal is ever applied or promoted.
- All real implementations live as candidates under `harnesses/candidates/`.
- No `.venv` / browser cache / runs / screenshots / secrets are committed.

## Next possible phase (none started — decision point)

a. **Approved Patch Application** — a human approves a proposal and the change is
   applied. **Blocked behind a human approval gate.** Hard prerequisites: must NOT
   modify stable directly; must apply only to a candidate workspace; must have
   human approval; must run targeted tests + regression; must follow the promotion
   policy; must keep a rollback. **Not started.**
b. **Human review / staging / stable promotion** of the shell-executing candidates.
c. **UI dashboard** (the `apps/` surface).
d. **Real provider implementation** (operator opt-in; still fail-closed by default).
