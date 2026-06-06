# Checkpoint: Phase 5 — Candidate Merge v0 (Candidate Workspace Only)

- **checkpoint name:** `checkpoint-phase-5-candidate-merge`
- **commit (candidate merge passed):** `b5ee165`
- **tag:** `checkpoint-phase-5-candidate-merge`

Frozen snapshot of the chain **human-reviewed apply workspace → candidate merge
workspace → rollback plan → promotion review package → no stable promotion**.
Documentation only — no runtime, candidate, stable skill, safety gate, or promotion
policy change.

## What is frozen

- **Candidate Merge v0 exists.** `scripts/repair_merge.py` +
  `src/repair/{merge_validator,candidate_merge,merge_report}.py` take a
  human-approved apply workspace and merge its proposed changes into a new candidate
  merge workspace.
- **`repair_merge.py` exists.**
- **Human-reviewed only.** Merge requires the `APPROVED_FOR_CANDIDATE_MERGE: true`
  marker plus a named `Reviewer:` in the apply workspace's
  `merge_approval_checklist.md`, AND an explicit `--approved` flag with a non-empty
  `--reviewer`. Missing any → fail closed (exit 3).
- **Candidate-workspace-only merge.** Changes are merged only into a fresh candidate
  merge workspace's `merged_changes/`. **No real repo target file is written.**
- **No active candidate modification.** No existing/active candidate runtime code is
  changed; the merge lands in a separate `_repair_merges/<id>/` workspace.
- **No stable modification.**
- **No safety_gate modification.**
- **No promotion_policy modification.**
- **No auto promotion. No staging promotion. No stable promotion.**
- **merged_changes created inside the merge workspace only** — copied from the apply
  workspace's `proposed_changes/`.
- **rollback_plan.md created** (`rollback_available=true`): because nothing live was
  touched, rollback is just deleting the merge workspace.
- **promotion_review_package.md created** — input to a human's future
  staging/stable decision.
- **Fixed test command allowlist.** The only commands `repair_merge.py` can run are
  a hardcoded constant (never apply-derived): targeted (`validate_structure`,
  `validate_workflows`, `run_unit_tests`) + regression (`vite_login_bug` demo,
  `fake_approved_patch_application` eval, `fake_repair_proposal_only` eval).
  Recorded by default; executed only on `--run-tests`.

## Results (frozen)

| Eval / check | Result |
|---|---|
| `fake_candidate_merge` (category `candidate_merge`) | **score 1.0** (11/11 criteria) |
| `repair_merge.py` without `--approved` / empty `--reviewer` | **rejected** (exit 3) |
| `repair_merge.py --dry-run` | preview only, no workspace |
| stable files modified | **none** |
| active candidate modified | **none** |
| promoted | **false** |
| `fake_approved_patch_application` | **still 1.0** |
| `fake_repair_proposal_only` | **still 1.0** |
| `fake_full_browser_plan_execution` (planner execution) | **still 1.0** (real browser via the gate) |
| `full_browser_vite_login_bug_e2e` / `run_demo vite_login_bug` | **still 1.0** |

- **secret hygiene: PASS.** **unit tests: 339/339.**

## Pipeline

```
approved apply workspace (merge_approval_checklist.md: APPROVED_FOR_CANDIDATE_MERGE + Reviewer)
  → apply manifest re-validation (workspace-only / not promoted / not stable-modified)
  → merge validation             (validate_merge: marker + reviewer + targets + secret)
  → CandidateMerge               merged_changes/ + merge_manifest.json + merge_report.md
                                 + rollback_plan.md + promotion_review_package.md +
                                 test_results.json
  → fixed test allowlist         recorded (executed only on --run-tests)
  → staging / stable promotion   NOT implemented (human-driven, future phase)
```

## Frozen constraints

- **stable skills / active candidate runtime / safety_gate / promotion_policy
  untouched** throughout.
- `repair_merge.py` is candidate-workspace-only: no raw shell, no stable write, no
  promote.
- Generated `_repair_proposals/`, `_repair_applications/`, and `_repair_merges/`
  workspaces are gitignored; no `.venv` / browser cache / runs / screenshots /
  secrets committed.

## Next possible phase (none started — decision point)

a. **Human Review + Staging Promotion** — a human reviews a candidate merge
   workspace + its promotion review package, verifies the rollback plan, runs
   targeted tests + regression, then the promotion policy moves a candidate toward
   `staging`. **Blocked behind regression, rollback verification, the promotion
   policy, and explicit operator approval.** Stable / safety / promotion invariants
   must hold. Not started.
b. **Stable Promotion** — only after a policy review (a later, separate gate).
c. **UI dashboard** (the `apps/` surface).
d. **Real provider implementation** (operator opt-in; still fail-closed by default).
