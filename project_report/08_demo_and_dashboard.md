# 08 — Demo and Dashboard

## Demo package

A single-entry showcase lives at [`../demo_package/README.md`](../demo_package/README.md)
(overview, architecture, safe demo commands, dashboard, phase timeline, safety
boundaries, next steps, and a teacher outline). It lists **only safe commands** —
no real API, no secret read, no stable promotion.

## Safe demo commands

```bash
python scripts/validate_workflows.py                 # all gates green
python scripts/run_demo.py --demo vite_login_bug     # sandboxed patch + tests → 1.0
python scripts/run_full_browser_gate.py --dry-run    # safe anywhere
python scripts/generate_dashboard_snapshot.py        # redacted snapshot from docs only
python scripts/validate_dashboard.py                 # read-only + no-secret checks
python scripts/run_dashboard_smoke.py --dry-run      # safe anywhere
python scripts/run_unit_tests.py                     # 453/453
```

Real-browser runs (`run_full_browser_gate.py`, `run_dashboard_smoke.py`) use the
project `.venv` and reach 1.0.

## Dashboard (read-only)

The dashboard (`ui_dashboard/`) renders a **redacted snapshot** of project status —
latest checkpoint, phase status, candidate status, eval status, epic/story status,
safety invariants, report links.

- **Snapshot generator** reads only redacted docs (`README` / `docs/` / `reports/` /
  `docs/epics/` / `candidate.yaml`); never reads `.env`, `password_and_api.txt`, or
  raw `runs/` traces; **refuses to write** on secret detection.
- **Read-only by construction:** renders via `textContent` (no `innerHTML`, no
  dynamic code); **no button / form / onclick / POST**; **no external network** (the
  smoke gate asserts only `127.0.0.1` requests); **no secret display**.
- **Real-browser smoke gate** (`run_dashboard_smoke.py`, `evals/dashboard/
  ui_dashboard_readonly_smoke.yaml`) loads it in a real Playwright browser, verifies
  the read-only properties, and tears down with **no lingering process** (score 1.0).

## Why the dashboard cannot act

There is no path from the UI to an action. Any real action (run an eval, approve a
repair, promote) is a **human terminal step** through the existing approval-gated
scripts. Browser/page content is untrusted and can never trigger a tool, repair, or
promotion.
