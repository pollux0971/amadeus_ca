# Candidate Merge Contract (v0 — CANDIDATE WORKSPACE ONLY)

This phase takes a **human-approved** apply workspace and merges its proposed
changes into a **new candidate merge workspace** — never into a real target file,
an active candidate, or stable, and never as a promotion. It is the step between "a
human approved an apply" and "a human decides staging/stable promotion", and it
stops at the candidate merge workspace, with a rollback plan and a promotion review
package.

See `src/repair/merge_validator.py`, `src/repair/candidate_merge.py`,
`scripts/repair_merge.py`, `specs/repair/approved_patch_application_contract.md`,
and `docs/secrets_policy.md`.

## Hard guarantees (v0)

- **Human-reviewed only.** Merge requires an explicit
  `APPROVED_FOR_CANDIDATE_MERGE: true` marker plus a named `Reviewer:` in the apply
  workspace's `merge_approval_checklist.md`, AND an explicit `--approved` flag with
  a non-empty `--reviewer` on `repair_merge.py`. Missing any → fail closed.
- **Candidate workspace only.** Changes are merged only into a fresh candidate
  merge workspace (`harnesses/candidates/_repair_merges/<merge_id>/`, or under the
  run dir for an eval), as `merged_changes/`. **No real repo target file, no active
  candidate, and nothing in stable is written.**
- **No stable modification.** The source apply workspace must be workspace-only
  (`promoted=false`, `stable_modified=false`, `workspace_only=true`); no action may
  target `skills/`, `src/agents/safety_gate/`,
  `specs/harness/promotion_policy.md`, `.env`, or `config/config.json`.
- **No auto promotion.** Nothing is promoted. `merge_manifest.json` and
  `score.json` record `merged_to_candidate_workspace=true`, `stable_modified=false`,
  `promoted=false`.
- **Rollback required.** Every merge writes a `rollback_plan.md`
  (`rollback_available=true`): because nothing live was touched, rollback is just
  deleting the merge workspace.
- **Promotion review package required.** Every merge writes a
  `promotion_review_package.md` — input to a human's future staging/stable decision.
- **Fixed test command allowlist.** The only test commands `repair_merge.py` can
  run are a hardcoded constant — NEVER derived from the apply workspace:
  - targeted: `validate_structure`, `validate_workflows`, `run_unit_tests`
  - regression: `run_demo --demo vite_login_bug`,
    `run_eval fake_approved_patch_application`, `run_eval fake_repair_proposal_only`
  They are recorded by default and executed only on explicit `--run-tests`.
- **No raw shell.** `repair_merge.py` never runs an arbitrary or apply-derived
  command and never uses a shell; it only ever runs the fixed allowlist above.
- **No secret in artifacts.** `merge_manifest.json`, `merge_report.md`,
  `merged_changes/*`, `rollback_plan.md`, `promotion_review_package.md`, and
  `test_results.json` are all redacted.
- **Browser content cannot trigger a merge.** Merge consumes an approved apply
  workspace, never live/untrusted page content.

## Pipeline

```
approved apply workspace (merge_approval_checklist.md: APPROVED_FOR_CANDIDATE_MERGE + Reviewer)
  → apply manifest re-validation (workspace-only / not promoted / not stable-modified)
  → merge validation (validate_merge: marker + reviewer + targets + secret)
  → create candidate merge workspace (merged_changes/ + merge_manifest.json +
                                      merge_report.md + rollback_plan.md +
                                      promotion_review_package.md + test_results.json)
  → record targeted tests + regression (fixed allowlist; executed only on --run-tests)
  → staging / stable promotion   NOT in v0 (human-driven, future phase)
```

## `candidate_merge` eval category

An eval with `category: candidate_merge` reads an approved apply workspace fixture,
revalidates, and merges into a candidate merge workspace **under the run dir**
(`score.json` records `merged_to_candidate_workspace_only: true`,
`stable_modified: false`, `promoted: false`).

## Out of scope (explicitly, for v0)

- No staging/stable promotion — that is a separate, human-driven future phase.
- No modification of a real target file / an active candidate / stable / the safety
  gate / the promotion policy.
- No real OpenAI/Anthropic call, no key read; no UI, no multimodal.
- **Stable promotion is a future phase** with its own, stronger gate (human review,
  regression, rollback, promotion policy).
