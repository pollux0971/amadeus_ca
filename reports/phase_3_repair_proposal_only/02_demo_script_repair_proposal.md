# Demo script — Repair Proposal (v0, proposal-only)

A short, reproducible walk-through of the Phase 3 chain: **failed eval → failure
analysis → fake repair proposal → candidate workspace → human approval gate**.

## Demo goal

Show that a failed eval can be turned into a **redacted, human-reviewable repair
proposal** in a candidate workspace — with **no apply, no stable change, no
promotion, and no real LLM** — and that asking to apply is explicitly rejected.

## Commands

```bash
# 1) Dry-run a proposal from a fake failure report — prints a redacted proposal,
#    writes nothing.
python scripts/repair_propose.py \
    --failure-report fixtures/repair/fake_failed_eval/summary.md \
    --marker FAKE_REPAIR_TEST_FAILED --dry-run

# 2) Run the proposal-only eval — analyze → propose → workspace (under the run dir).
python scripts/run_eval.py --task evals/repair/fake_repair_proposal_only.yaml

# 3) Confirm apply is refused.
python scripts/repair_propose.py \
    --failure-report fixtures/repair/fake_failed_eval/summary.md --apply ; echo "exit=$?"
```

## Expected output

1. **`repair_propose ... --dry-run`** → a `# Repair Proposal` markdown block headed
   `PROPOSAL ONLY — NOT APPLIED — HUMAN APPROVAL REQUIRED`, an action table
   (`update_candidate`, `add_test`), and `[DRY-RUN] proposal printed; no workspace
   written, nothing applied.` (exit 0).
2. **`run_eval ... fake_repair_proposal_only`** → `[PASS] fake_repair_proposal_only
   score=1.0` with all 8 criteria met (`failure_analyzed`, `proposal_created`,
   `proposal_valid`, `candidate_workspace_created`, `proposal_not_applied`,
   `no_stable_files_modified`, `no_safety_or_promotion_modified`,
   `no_secret_in_proposal`). `score.json` records `applied: false`,
   `promoted: false`.
3. **`repair_propose ... --apply`** → `[REJECTED] --apply is not supported in Auto
   Repair Loop v0 …` and **exit=3**. Nothing is applied.

## How to explain it

- **Failure analyzer.** Reads only the run's `score.json` / `summary.md` /
  `trace.jsonl` (metadata), **redacts everything it keeps**, and never opens
  `.env`, a password file, or any secret. It classifies the failure
  (`test_failed`, `missing_artifact`, `console_error`, …). Browser/untrusted page
  content is never an input, so page text can never trigger a repair.
- **Fake repair planner.** Deterministic and offline — it depends on
  `FakeLLMProvider` (no network, no env-var key read, no real API call). A marker
  (or the analyzer's failure_type) selects a fixed proposal. There is no real
  model reasoning; the demo is fully reproducible.
- **Proposal validator.** The trust gate: it rejects any action targeting a stable
  skill, the safety gate, or the promotion policy; rejects shell / eval / delete
  actions; requires approval for high-risk; fails on secret-looking content; and
  **rejects `applied=true`**. Only allowlisted action types against allowed roots
  (candidates / tests / evals / docs / reports) survive.
- **Candidate workspace.** Writes the proposal, the failure analysis, an
  `approval_checklist.md`, and a proposal-only `README.md`. **No target file is
  touched** — the workspace is just somewhere for a human to read and decide.
- **Why this is NOT auto-repair yet.** v0 stops at the proposal. It applies
  nothing, edits no candidate/stable code, runs no test, and promotes nothing.
  `--apply` is rejected and there is no `scripts/repair_apply.py`. Applying a
  proposal is a separate, human-approved, not-yet-implemented phase.

## Safety notes

- Default is dry-run for the script; the eval writes its workspace under the run
  dir (never polluting the repo).
- All artifacts are redacted; no secret reaches disk.
- This demo touches no stable skill, `safety_gate`, or `promotion_policy`.
