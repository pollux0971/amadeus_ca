# Phase 3 — Auto Repair Loop v0 (Proposal Only)

This phase adds the **minimal, safe skeleton** of an auto-repair loop: it can read
a failed eval and produce a **repair proposal** for a human to review. It does
**not** apply anything. It builds on Phase 2A (planner execution bridge).

## Why proposal-only first

Auto-repair is the most dangerous capability in the system: a loop that edits code
and re-runs could, if unchecked, modify a stable skill, weaken the safety gate, or
promote an unreviewed change. So v0 deliberately stops at the *proposal*:

- A human stays in the loop — every change is gated by an `approval_checklist.md`.
- Nothing is applied, executed, or promoted; no stable file is touched.
- The blast radius is a redacted proposal in a candidate workspace.

This lets us validate the analysis → proposal → workspace chain safely before any
apply capability is ever considered.

## What it does NOT do (hard limits)

- **No apply.** No `scripts/repair_apply.py`; `--apply` is rejected (non-zero).
- **No stable modification.** Targets must be in `harnesses/candidates/`, `tests/`,
  `evals/`, `docs/`, `reports/`; `skills/`, `src/agents/safety_gate/`, and
  `specs/harness/promotion_policy.md` are forbidden.
- **No auto promotion, no autonomous replan.**
- **No real API call, no env-var key read** — fake provider only.
- **No direct shell** in a proposal; action types are an allowlist.

## How a repair proposal is produced

```
failed eval / failure_report
  → FailureAnalyzer      read score.json / summary.md / trace.jsonl (redacted), classify
  → FakeRepairPlanner    marker → deterministic RepairProposal (fake, offline)
  → proposal_validator   allowlist + protected paths + secret + applied=false
  → candidate_workspace  write repair_proposal.{json,md} + failure_analysis.json
                         + approval_checklist.md + README (proposal-only)
  → approval gate        a human clears the checklist (NOT in v0)
```

Run it:

```bash
python scripts/repair_propose.py \
    --failure-report fixtures/repair/fake_failed_eval/summary.md \
    --marker FAKE_REPAIR_TEST_FAILED --dry-run        # prints a redacted proposal, writes nothing
python scripts/run_eval.py --task evals/repair/fake_repair_proposal_only.yaml   # → 1.0
```

## Results

| Eval | Category | Score | Notes |
|---|---|---|---|
| `fake_repair_proposal_only` | repair_proposal | **1.0** | analyze → proposal → workspace; `applied: false` |

Success criteria met: `failure_analyzed`, `proposal_created`, `proposal_valid`,
`candidate_workspace_created`, `proposal_not_applied`, `no_stable_files_modified`,
`no_safety_or_promotion_modified`, `no_secret_in_proposal`.

## Remaining risks / limits

- **No apply yet.** The proposal must be applied by a human; there is no automated
  application path.
- **Markers are deterministic, not semantic.** `FakeRepairPlanner` selects a fixed
  proposal per marker / failure_type; it does not reason about arbitrary code.
- **Fake provider only.** No real model is consulted.
- **Stable promotion still requires human review** — unchanged.

## Next phase (not started)

**Approved patch application** — a separate, gated phase: a human approves a
proposal, the change is made *in a candidate workspace* (never stable directly),
its eval runs, and only then does the normal promotion policy apply. Apply must
have its own approval gate and must never touch stable, the safety gate, or the
promotion policy automatically.
