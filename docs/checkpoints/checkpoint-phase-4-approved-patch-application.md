# Checkpoint: Phase 4 — Approved Patch Application v0 (Workspace Only)

- **checkpoint name:** `checkpoint-phase-4-approved-patch-application`
- **commit (approved apply passed):** `0eca9de`
- **tag:** `checkpoint-phase-4-approved-patch-application`

Frozen snapshot of the chain **human-approved proposal → workspace-only apply →
proposed_changes → fixed test allowlist → apply report → no merge / no
promotion**. Documentation only — no runtime, candidate, stable skill, safety
gate, or promotion policy change.

## What is frozen

- **Approved Patch Application v0 exists.** `scripts/repair_apply.py` +
  `src/repair/{apply_validator,patch_application,apply_report}.py` take an approved
  repair proposal and materialize the approved changes into an apply workspace.
- **`repair_apply.py` exists** (it did not at Phase 3 — see that checkpoint's
  historical "no repair_apply.py" note).
- **Human-approved only.** Apply requires the
  `APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY: true` marker plus a named `Reviewer:` in
  the proposal workspace's `approval_checklist.md`, AND an explicit `--approved`
  flag. Missing either → fail closed (`--approved`-less apply exits 3).
- **Workspace-only apply.** Changes are materialized only under the apply
  workspace's `proposed_changes/`. **No real repo target file is written.**
- **No stable modification.** No target may be under `skills/`,
  `src/agents/safety_gate/`, `specs/harness/promotion_policy.md`, `.env`, or
  `config/config.json`. Targets stay inside `harnesses/candidates/`, `tests/`,
  `evals/`, `docs/`, `reports/`.
- **No safety_gate modification. No promotion_policy modification.**
- **No auto promotion. No merge.** `apply_manifest.json` and `score.json` record
  `promoted: false` and `stable_modified: false`; nothing is merged into the repo.
- **proposed_changes created inside the apply workspace only** — one materialized
  file per non-noop action; noop is recorded, not materialized.
- **Fixed test command allowlist.** The only commands `repair_apply.py` can run
  are a hardcoded constant (never proposal-derived):
  `validate_structure`, `validate_workflows`, `run_unit_tests`, and the
  `vite_login_bug` demo. Recorded by default; executed only on `--run-tests`.

## Results (frozen)

| Eval / check | Result |
|---|---|
| `fake_approved_patch_application` (category `approved_patch_application`) | **score 1.0** (9/9 criteria) |
| `repair_apply.py` without `--approved` | **rejected** (exit 3) |
| `repair_apply.py --dry-run` | preview only, no workspace |
| stable files modified | **none** |
| promoted | **false** |
| `fake_repair_proposal_only` | **still 1.0** |
| `fake_full_browser_plan_execution` (planner execution) | **still 1.0** (real browser via the gate) |
| `full_browser_vite_login_bug_e2e` / `run_demo vite_login_bug` | **still 1.0** |

- **secret hygiene: PASS.** **unit tests: 303/303.**

## Pipeline

```
approved repair proposal workspace (approval_checklist.md: APPROVED_… + Reviewer)
  → proposal re-validation        (validate_proposal)
  → apply validation              (validate_for_apply: marker + reviewer + apply
                                   allowlist + protected-target block + secret)
  → ApplyWorkspace                proposed_changes/ + apply_manifest.json +
                                   apply_report.md + test_results.json + README
  → fixed test allowlist          recorded (executed only on --run-tests)
  → merge / promotion             NOT implemented (human-driven, future phase)
```

## Frozen constraints

- **stable skills / safety_gate / promotion_policy untouched** throughout.
- `repair_apply.py` is workspace-only: no raw shell, no stable write, no promote.
- Generated `_repair_proposals/` and `_repair_applications/` workspaces are
  gitignored; no `.venv` / browser cache / runs / screenshots / secrets committed.

## Next possible phase (none started — decision point)

a. **Merge + Promotion** — a human reviews an apply workspace and merges the
   proposed change into a **candidate** (never stable directly), runs targeted
   tests + regression, produces a rollback plan, then the promotion policy applies.
   **Blocked behind human review, targeted regression, a rollback plan, and the
   promotion policy.** Stable / safety / promotion invariants must hold. Not started.
b. **Human review / staging / stable promotion** of the shell-executing candidates.
c. **UI dashboard** (the `apps/` surface).
d. **Real provider implementation** (operator opt-in; still fail-closed by default).
