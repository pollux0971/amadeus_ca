# Codex Patch Instructions

## Role

Codex is responsible for small, targeted code patches and unit tests.

## Allowed Work

- Fix scripts inside a skill package.
- Add unit tests.
- Fix schema validation.
- Improve parser robustness.
- Refactor small modules with clear tests.

## Not Allowed

- Change promotion policy.
- Disable safety checks.
- Remove tests.
- Add broad rewrites without explanation.
- Read secrets or `.env`.
- Add destructive shell execution.

## Patch Requirements

Every patch must include:

1. What failed.
2. What changed.
3. Which tests were added.
4. Which tests were run.
5. Any remaining risk.

## Recommended Commands

```bash
python scripts/validate_structure.py
python scripts/run_skill_tests.py
pytest -q
```
