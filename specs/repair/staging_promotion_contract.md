# Staging Promotion Contract (v0 — STAGING WORKSPACE ONLY)

This phase takes a **human-approved** candidate merge workspace and promotes its
merged changes into a **staging promotion workspace** — never into a real target
file, an active candidate, or stable, and never as a stable promotion. It is the
step between "a human approved a candidate merge" and "a human decides stable
promotion", and it stops at the staging workspace, with rollback verification, a
regression record, and a stable-promotion checklist.

See `src/repair/staging_validator.py`, `src/repair/staging_promotion.py`,
`scripts/staging_promote.py`, `specs/repair/candidate_merge_contract.md`, and
`docs/secrets_policy.md`.

## Hard guarantees (v0)

- **Human-reviewed only.** Staging requires an explicit
  `APPROVED_FOR_STAGING_PROMOTION: true` marker plus a named `Reviewer:` in the
  merge workspace's `staging_approval_checklist.md`, AND an explicit `--approved`
  flag with a non-empty `--reviewer` on `staging_promote.py`. Missing any → fail
  closed.
- **Staging workspace only.** Changes are promoted only into a fresh staging
  workspace (`harnesses/candidates/_staging_promotions/<staging_id>/`, or under the
  run dir for an eval), as `staged_changes/`. **No real repo target file, no active
  candidate, and nothing in stable is written.**
- **No stable modification.** The source merge workspace must be
  candidate-workspace-only (`merged_to_candidate_workspace=true`,
  `stable_modified=false`, `promoted=false`, `rollback_available=true`); no action
  may target `skills/`, `src/agents/safety_gate/`,
  `specs/harness/promotion_policy.md`, `.env`, or `config/config.json`.
- **No stable promotion. No auto promotion.** Nothing is stable-promoted.
  `staging_manifest.json` and `score.json` record `staged=true`,
  `stable_modified=false`, `stable_promoted=false`, `active_candidate_modified=false`.
- **Rollback verification required.** Every staging step writes a
  `rollback_verification.md` recording whether the source rollback plan is present
  (`rollback_verified`); because nothing live was touched, rolling back staging is
  deleting the staging workspace.
- **Regression required.** Every staging step records a regression result
  (`regression_results.json`) over the fixed allowlist; a `stable_promotion_checklist.md`
  is produced for the human's future stable decision.
- **Fixed test command allowlist.** The only test commands `staging_promote.py` can
  run are a hardcoded constant — NEVER derived from the merge workspace:
  - targeted: `validate_structure`, `validate_workflows`, `run_unit_tests`
  - regression: `run_demo --demo vite_login_bug`, `run_eval fake_candidate_merge`,
    `run_eval fake_approved_patch_application`, `run_eval fake_repair_proposal_only`,
    `run_eval fake_full_browser_plan_execution`
  They are recorded by default and executed only on explicit `--run-tests`.
- **No raw shell.** `staging_promote.py` never runs an arbitrary or merge-derived
  command and never uses a shell; it only ever runs the fixed allowlist above.
- **No secret in artifacts.** `staging_manifest.json`, `staging_report.md`, the
  staged `staged_changes/*`, `rollback_verification.md`, `regression_results.json`,
  and `stable_promotion_checklist.md` are all redacted.
- **Browser content cannot trigger a promotion.** Staging consumes an approved merge
  workspace, never live/untrusted page content.
- **Promotion policy still required.** Reaching staging does NOT satisfy the
  promotion policy; stable promotion remains a separate, policy-gated, human-driven
  phase.

## Pipeline

```
approved candidate merge workspace (staging_approval_checklist.md: APPROVED_FOR_STAGING_PROMOTION + Reviewer)
  → merge manifest re-validation (candidate-workspace-only / not promoted / not stable-modified / rollback_available)
  → staging validation           (validate_staging: marker + reviewer + rollback/package present + targets + secret)
  → create staging workspace      staged_changes/ + staging_manifest.json + staging_report.md
                                  + rollback_verification.md + regression_results.json +
                                  stable_promotion_checklist.md
  → record targeted tests + regression (fixed allowlist; executed only on --run-tests)
  → stable promotion             NOT in v0 (human-driven, policy-gated, future phase)
```

## `staging_promotion` eval category

An eval with `category: staging_promotion` reads an approved candidate merge
workspace fixture, revalidates, and promotes into a staging workspace **under the
run dir** (`score.json` records `staged_to_workspace_only: true`,
`stable_modified: false`, `stable_promoted: false`, `active_candidate_modified: false`).

## Out of scope (explicitly, for v0)

- No stable promotion — that is a separate, human-driven, policy-gated future phase.
- No modification of a real target file / an active candidate / stable / the safety
  gate / the promotion policy.
- No real OpenAI/Anthropic call, no key read; no UI, no multimodal.
- **Stable promotion is a future phase** with its own, stronger gate (human review,
  full regression, verified rollback, promotion policy sign-off).
