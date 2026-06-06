# Run Summary

Task `fake_failed_eval` — **FAIL** (score 0.6667).

This is a FAKE, redacted failure fixture used to exercise the repair proposal
pipeline. It contains no secret and no real run data.

## Criteria

- [x] project_inspected
- [x] source_file_patched
- [ ] tests_pass

## Failure

- root_cause: the patched function still returns the wrong value; the test
  `test_login.py` asserts a token and got the raw user.
- category: test_failed

> Fixture only — nothing here is applied or executed.
