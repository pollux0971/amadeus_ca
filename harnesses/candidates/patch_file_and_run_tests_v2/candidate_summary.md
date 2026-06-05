# Candidate Summary — patch_file_and_run_tests_v2

## 1. What failed before

v1 already took `vite_login_bug` to 1.0, but it was **demo-specific**: the runner
hard-coded the `src/App.jsx` fix (read the worked example or do fixed string
replacements on that one file). It could not patch any other bug, supported no
declarative patch format, and `candidate_summary.md` (v1) explicitly recommended
**not** promoting it. So the open problem was generality, not the vite score.

## 2. What changed

v2 replaces the hard-coded fix with a **plan-driven engine** — no fixture-specific
code anywhere in the runner:

- `patch_plan` schema with two patch types: `replace_text` and `unified_diff`
  (includes a small, dependency-free unified-diff applier).
- Plans are declarative YAML resolved by fixture basename from `plans/`
  (`plans/vite_login_bug.yaml`, `plans/py_calc_bug.yaml`), or passed inline.
- Copies the fixture to an isolated sandbox, applies patches there, and emits
  `patch.diff` from a real before/after diff of every touched file.
- Runs the plan's `test_command` through the Safety Gate; writes `test.log`.
- Writes `result.json` including a `failure_reason` on every failure path
  (`plan_not_found`, `target_file_not_found`, `target_text_not_found`,
  `diff_apply_failed`, `command_blocked`, `no_test_command`, `test_failed`,
  `unsafe_path`).
- Ships an in-candidate non-vite fixture (`fixtures/py_calc_bug`) patched via
  `unified_diff`, proving the runner is not tied to App.jsx.

Harness infrastructure (not the stable skill / safety gate / promotion policy):
- `src/skills_runtime/executor.py`: the overlay resolver is now **version-aware**
  — among active candidates for one skill, the highest `version` wins. This lets
  v2 supersede v1 **without editing v1** (v1 stays `active: true`, `version` 1).

## 3. Tests added

`harnesses/candidates/patch_file_and_run_tests_v2/tests/test_patch_runner_v2.py`:
- `test_replace_text_patch_succeeds`
- `test_unified_diff_patch_succeeds` (uses the in-candidate non-vite fixture)
- `test_missing_target_file_fails`
- `test_text_not_found_fails`
- `test_blocked_test_command_fails_safely`
- `test_source_fixtures_are_not_mutated`
- `test_unified_diff_applier_unit`

## 4. Tests run

- `python scripts/validate_structure.py` — PASS
- `python scripts/validate_workflows.py` — PASS
- `python scripts/run_skill_tests.py` — 5/5 PASS
- `python scripts/run_unit_tests.py` — **49/49 PASS** (42 prior + 7 v2)
- `python scripts/run_demo.py --demo vite_login_bug` — score 1.0
- Regression (candidates disabled) — vite reverts to stable 0.667 / placeholder
- Regression (candidates enabled) — vite 1.0, patch produced by v2

## 5. Metrics before/after

| Metric | Before (v1) | After (v2) |
|---|---|---|
| vite_login_bug score | 1.0 | 1.0 |
| Fixtures proven | 1 (vite) | 2 (vite + py_calc_bug) |
| Patch types supported (as data) | 0 (hard-coded) | 2 (replace_text, unified_diff) |
| Fixture-specific code branches | yes (App.jsx) | 0 |
| Adding a new bug needs | code change | a new plan file |
| Candidates-disabled regression | 0.667 | 0.667 |
| Unit tests | 42 | 49 |

## 6. Remaining risks

- Executes a shell `test_command` (through the Safety Gate) — real but narrow
  execution surface.
- The unified-diff applier handles clean diffs (exact context/removal match); it
  is not a fuzzy/offset-tolerant patcher. Bad diffs fail loudly with a reason.
- `test_command` defaults still come from `inspect_project` in the orchestrator
  flow, so non-node fixtures driven end-to-end would need a runnable test command
  (the new fixture is proven via unit tests + plan, not a full orchestrator eval).

## 7. Promotion recommendation

**Keep at `dev`; do not promote yet.** Per `promotion_policy.md`, shell execution
requires human review. v2 removes the "demo-specific" blocker and is a credible
promotion candidate once: (a) it is exercised by ≥1 non-vite eval end-to-end, and
(b) human review signs off on the sandboxed shell execution. v1 can then be
retired (`active: false`).

## 8. Files modified

New (candidate v2):
- `harnesses/candidates/patch_file_and_run_tests_v2/candidate.yaml`
- `.../scripts/patch_file_and_run_tests.py`
- `.../plans/vite_login_bug.yaml`, `.../plans/py_calc_bug.yaml`
- `.../fixtures/py_calc_bug/calc.py`, `.../fixtures/py_calc_bug/test_calc.py`
- `.../SKILL.md`, `.../tests/test_patch_runner_v2.py`, `.../candidate_summary.md`

Changed (harness infrastructure only):
- `src/skills_runtime/executor.py` — version-aware overlay resolution.

Untouched (per constraints): all stable `skills/`, `safety_gate`,
`promotion_policy`, and candidate **v1** (still `active`, superseded by version).
