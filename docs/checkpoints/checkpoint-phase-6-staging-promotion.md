# Checkpoint: Phase 6 — Staging Promotion v0 (Staging Workspace Only)

- **checkpoint name:** `checkpoint-phase-6-staging-promotion`
- **commit (staging promotion passed):** `78ecae3`
- **tag:** `checkpoint-phase-6-staging-promotion`

Frozen snapshot of the chain **human-reviewed candidate merge workspace → staging
promotion workspace → rollback verification → stable promotion checklist → no stable
promotion**. Documentation only — no runtime, candidate, stable skill, safety gate,
or promotion policy change.

## What is frozen

- **Staging Promotion v0 exists.** `scripts/staging_promote.py` +
  `src/repair/{staging_validator,staging_promotion,staging_report}.py` take a
  human-approved candidate merge workspace and promote its merged changes into a new
  staging workspace.
- **`staging_promote.py` exists.**
- **Human-reviewed only.** Staging requires the `APPROVED_FOR_STAGING_PROMOTION: true`
  marker plus a named `Reviewer:` in the merge workspace's
  `staging_approval_checklist.md`, AND an explicit `--approved` flag with a non-empty
  `--reviewer`. Missing any → fail closed (exit 3).
- **Staging-workspace-only.** Changes are promoted only into a fresh staging
  workspace's `staged_changes/`. **No real repo target file is written.**
- **No active candidate modification.** No existing/active candidate runtime code is
  changed; staging lands in a separate `_staging_promotions/<id>/` workspace.
- **No stable modification.**
- **No safety_gate modification.**
- **No promotion_policy modification.**
- **No auto promotion. No stable promotion.**
- **staged_changes created inside the staging workspace only** — copied from the merge
  workspace's `merged_changes/`.
- **rollback_verification.md created** (records `rollback_verified`): because nothing
  live was touched, rolling back staging is just deleting the staging workspace.
- **stable_promotion_checklist.md created** — input to a human's future stable
  decision.
- **Fixed test command allowlist.** The only commands `staging_promote.py` can run are
  a hardcoded constant (never merge-derived): targeted (`validate_structure`,
  `validate_workflows`, `run_unit_tests`) + regression (`vite_login_bug` demo,
  `fake_candidate_merge`, `fake_approved_patch_application`, `fake_repair_proposal_only`,
  `fake_full_browser_plan_execution` evals). Recorded by default; executed only on
  `--run-tests`.

## Results (frozen)

| Eval / check | Result |
|---|---|
| `fake_staging_promotion` (category `staging_promotion`) | **score 1.0** (11/11 criteria) |
| `staging_promote.py` without `--approved` / empty `--reviewer` | **rejected** (exit 3) |
| `staging_promote.py --dry-run` | preview only, no workspace |
| stable files modified | **none** |
| active candidate modified | **none** |
| stable promoted | **false** |
| `fake_candidate_merge` | **still 1.0** |
| `fake_approved_patch_application` | **still 1.0** |
| `fake_repair_proposal_only` | **still 1.0** |
| `fake_full_browser_plan_execution` (planner execution) | **still 1.0** (real browser via the gate) |
| `full_browser_vite_login_bug_e2e` / `run_demo vite_login_bug` | **still 1.0** |

- **secret hygiene: PASS.** **unit tests: 376/376.**

## Pipeline

```
approved candidate merge workspace (staging_approval_checklist.md: APPROVED_FOR_STAGING_PROMOTION + Reviewer)
  → merge manifest re-validation (candidate-workspace-only / not promoted / not stable-modified / rollback_available)
  → staging validation           (validate_staging: marker + reviewer + rollback/package present + targets + secret)
  → StagingPromotion             staged_changes/ + staging_manifest.json + staging_report.md
                                 + rollback_verification.md + regression_results.json +
                                 stable_promotion_checklist.md
  → fixed test allowlist         recorded (executed only on --run-tests)
  → stable promotion             NOT implemented (human-driven, policy-gated, future phase)
```

## Frozen constraints

- **stable skills / active candidate runtime / safety_gate / promotion_policy
  untouched** throughout.
- `staging_promote.py` is staging-workspace-only: no raw shell, no stable write, no
  stable promote.
- Generated `_repair_proposals/`, `_repair_applications/`, `_repair_merges/`, and
  `_staging_promotions/` workspaces are gitignored; no `.venv` / browser cache / runs
  / screenshots / secrets committed.

## Next possible phase (none started — decision point)

a. **Stable Promotion** — a human reviews a staging workspace + its
   stable-promotion checklist, confirms the verified rollback and full regression,
   completes the human shell-execution review, then the promotion policy moves a
   candidate to `stable`. **Blocked behind human review, full regression, rollback
   verification, shell-execution review, the promotion policy, and explicit operator
   approval.** Stable / safety / promotion invariants must hold. Not started.
b. **UI dashboard** (the `apps/` surface).
c. **Real provider implementation** (operator opt-in; still fail-closed by default).
