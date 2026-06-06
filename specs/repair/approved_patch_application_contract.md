# Approved Patch Application Contract (v0 — WORKSPACE ONLY)

This phase takes a **human-approved** repair proposal and materializes the
approved changes into an **apply workspace** — never into a real target file,
never into stable, and never as a promotion. It is the step between "a human
approved a proposal" and "a human merges/promotes it", and it stops at the
workspace.

See `src/repair/apply_validator.py`, `src/repair/patch_application.py`,
`scripts/repair_apply.py`, `specs/repair/repair_loop_contract.md`, and
`docs/secrets_policy.md`.

## Hard guarantees (v0)

- **Human-approved only.** Apply requires an explicit approval marker
  `APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY: true` plus a named `Reviewer:` in the
  proposal workspace's `approval_checklist.md`, AND an explicit `--approved` flag
  on `repair_apply.py`. Missing either → fail closed.
- **Candidate / apply workspace only.** Changes are materialized only under an
  apply workspace (`harnesses/candidates/_repair_applications/<apply_id>/`, or
  under the run dir for an eval), inside `proposed_changes/`. **No real repo
  target file is written or overwritten.**
- **No stable modification.** No action may target a stable skill (`skills/`), the
  safety gate (`src/agents/safety_gate/`), or the promotion policy
  (`specs/harness/promotion_policy.md`); also never `.env` or `config/config.json`.
  Targets must stay inside `harnesses/candidates/`, `tests/`, `evals/`, `docs/`,
  `reports/`.
- **No auto promotion.** Nothing is promoted or merged. `apply_manifest.json` and
  `score.json` record `promoted: false` and `stable_modified: false`.
- **Apply action subset.** Apply is allowed only for action types
  `update_candidate`, `add_test`, `update_eval`, `update_docs` (and `noop`, which
  is recorded but materializes nothing). `modify_stable_skill`,
  `modify_safety_gate`, `modify_promotion_policy`, `raw_shell`, `direct_command`,
  and `delete_file` are rejected.
- **Fixed test command allowlist.** The only test commands `repair_apply.py` can
  run are a hardcoded constant — NEVER derived from a proposal:
  - `python scripts/validate_structure.py`
  - `python scripts/validate_workflows.py`
  - `python scripts/run_unit_tests.py`
  - `python scripts/run_demo.py --demo vite_login_bug`
  They are recorded by default and executed only on explicit `--run-tests`.
- **No raw shell.** `repair_apply.py` never runs an arbitrary or proposal-derived
  command and never uses a shell; it only ever runs the fixed allowlist above
  (as argv, no shell).
- **No secret in artifacts.** `apply_manifest.json`, `apply_report.md`,
  `proposed_changes/*`, and `test_results.json` are all redacted.
- **Browser content cannot trigger an apply.** Apply consumes an approved proposal
  workspace, never live/untrusted page content.

## Pipeline

```
approved repair proposal workspace
  → approval_checklist.md has APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY: true + Reviewer
  → proposal re-validation (validate_proposal)
  → apply validation (validate_for_apply: marker + reviewer + apply allowlist + targets)
  → create apply workspace (proposed_changes/ + apply_manifest.json + apply_report.md
                            + test_results.json + README) — NO target file touched
  → record targeted tests (fixed allowlist; executed only on --run-tests)
  → (merge / promote)   NOT in v0
```

## `approved_patch_application` eval category

An eval with `category: approved_patch_application` reads an approved proposal
workspace fixture, revalidates, and materializes the apply workspace **under the
run dir** (`score.json` records `applied_to_workspace_only: true`,
`stable_modified: false`, `promoted: false`).

## Out of scope (explicitly, for v0)

- No merge of an apply workspace into the repo, no promotion.
- No modification of stable / a real target file / the safety gate / the
  promotion policy.
- No rollback tooling and no real-model reasoning yet (rollback / merge /
  promotion are future, human-driven phases).
- No real OpenAI/Anthropic call, no key read; no UI, no multimodal.
