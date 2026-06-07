# 03 — Demo Commands (safe to run live)

All commands below are **safe to demonstrate**: read-only or sandboxed, no real API
call, no secret read, no stable promotion. Real-browser steps use the project
`.venv` (Playwright + Chromium); `--dry-run` forms are safe anywhere.

## Gates & structure

```bash
python scripts/validate_structure.py
python scripts/validate_workflows.py        # runs all doc/gate validators
python scripts/check_secret_hygiene.py
python scripts/validate_config.py
```

## Fake provider smoke (no real API)

```bash
python scripts/llm_smoke.py --fake-only     # always the fake provider; fail-closed
```

## Vertical-slice demo (sandboxed patch + tests)

```bash
python scripts/run_demo.py --demo vite_login_bug    # → score 1.0
```

## Real-browser gate (preview anywhere; full run needs .venv)

```bash
python scripts/run_full_browser_gate.py --dry-run   # safe anywhere; launches nothing
# full run (Playwright env): python scripts/run_full_browser_gate.py
```

## Dashboard (read-only)

```bash
python scripts/generate_dashboard_snapshot.py       # redacted snapshot from docs only
python scripts/validate_dashboard.py                # read-only + no-secret checks
python scripts/run_dashboard_smoke.py --dry-run     # safe anywhere; runs nothing
# real-browser smoke (Playwright env): python scripts/run_dashboard_smoke.py  → 1.0
```

## Tests

```bash
python scripts/run_skill_tests.py
python scripts/run_unit_tests.py
```

## NOT shown / NOT allowed in a demo

- ❌ No real OpenAI/Anthropic API call (no real-provider env opt-in run; fake only).
- ❌ No reading of `.env` key values or `/data/python/computer_agent_v5/password_and_api.txt`.
- ❌ No stable promotion / no merge into stable (blocked behind human + policy gates).
- ❌ No raw shell / direct command outside these fixed scripts.

These exclusions are enforced by `scripts/validate_demo_package.py` (the demo command
list is checked to contain no real-API / secret-file / stable-promotion command).
