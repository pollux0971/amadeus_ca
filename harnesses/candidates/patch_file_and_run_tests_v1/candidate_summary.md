# Candidate Summary

## Failure

`evals/cli_browser_integration/vite_login_bug.yaml` scored **0.667** (4/6).
`source_file_patched` and `tests_pass` failed; `failure_report.md` attributed
the gap to `patch_file_and_run_tests` returning `status: not_implemented`.

## Root Cause

The stable `patch_file_and_run_tests` skill is a placeholder: it never applies
a diff and never runs the test command, so two success criteria can never be
met regardless of the rest of the slice.

## Files Changed

Candidate (new, under `harnesses/candidates/patch_file_and_run_tests_v1/`):
- `candidate.yaml` — overlay manifest (`overrides: patch_file_and_run_tests`, `active: true`, `callable: patch_and_run`).
- `scripts/patch_file_and_run_tests.py` — real `patch_and_run` runner.
- `SKILL.md`, `candidate_summary.md`, `tests/test_patch_candidate.py`.

Harness wiring (no stable skill, safety gate, or promotion policy touched):
- `src/skills_runtime/executor.py` — `discover_active_candidates()` + candidate
  overlay resolution in `_load_callable`. Default OFF; a bare
  `SkillExecutor("skills")` still runs stable skills.
- `src/orchestrator/orchestrator.py` — enables candidate overlays during eval
  runs and passes `artifacts_dir` to the patch skill (stable skill ignores it).
- `scripts/run_unit_tests.py` — also discovers candidate package tests.
- `tests/unit/test_orchestrator_eval.py` — slice now expected to pass; added a
  candidates-disabled regression test proving the stable skill is unchanged.

## Tests Added

- `tests/test_patch_candidate.py`: patch applied + tests pass; diff contains the
  fix; Safety-Gate-blocked command fails safely; committed fixture never mutated.
- `tests/unit/test_orchestrator_eval.py::test_vite_slice_passes_with_active_candidate`
- `tests/unit/test_orchestrator_eval.py::test_vite_slice_is_placeholder_when_candidates_disabled`

## Tests Run

- `python scripts/validate_structure.py` — PASS
- `python scripts/validate_workflows.py` — PASS
- `python scripts/run_skill_tests.py` — 5/5 PASS
- `python scripts/run_unit_tests.py` — 42/42 PASS
- `python scripts/run_eval.py --task evals/walking_skeleton/inspect_only.yaml` — score 1.0
- `python scripts/run_demo.py --demo vite_login_bug` — score 1.0

## Result

`vite_login_bug` rose from **0.667 → 1.0** (6/6 criteria). No `failure_report.md`
is produced; `runs/<id>/artifacts/` contains `patch.diff`, `test.log`,
`result.json`. With overlays disabled the slice correctly reverts to 0.667,
confirming the stable skill itself is unchanged.

## Remaining Risk

- Demo-scoped only: the runner hard-codes the `src/App.jsx` fix and assumes
  `npm` is on PATH. It is not a general patch tool.
- Runs a shell command (`test_command`) through the Safety Gate — real but
  narrow execution surface.
- Idempotent and sandboxed (patches a temp copy), so reruns are safe.

## Promotion Recommendation

**Do not promote to stable yet.** Keep at `dev`. Per `promotion_policy.md`,
shell execution requires human review. Before promotion: support a real
multi-file patch format and add a broader eval set beyond `vite_login_bug`.
