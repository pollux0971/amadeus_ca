# 04 — Dashboard Demo (read-only)

The dashboard (`ui_dashboard/`) is a **read-only** static view of a **redacted
snapshot** of project status. It triggers nothing.

## Generate the snapshot

```bash
python scripts/generate_dashboard_snapshot.py
```

Reads **only** redacted docs (`README` / `docs/` / `reports/` / `docs/epics/` /
`candidate.yaml`). It does **not** read `.env`, `password_and_api.txt`, or raw
`runs/` traces; makes no API call; runs no shell; and **refuses to write** if any
secret-looking value is detected. Output: `ui_dashboard/data/dashboard_snapshot.json`
(gitignored; the tracked example is `dashboard_snapshot.example.json`).

## Validate + view

```bash
python scripts/validate_dashboard.py     # read-only / no-secret / required-keys checks
# then open ui_dashboard/static/index.html in a browser (served read-only)
```

## Real-browser smoke

```bash
python scripts/run_dashboard_smoke.py --dry-run   # safe anywhere
python scripts/run_dashboard_smoke.py             # Playwright env → score 1.0
```

Starts an **in-process** localhost static server (no shell), opens the dashboard in a
real Playwright browser, verifies it stays read-only, then tears down with **no
lingering process**.

## What the dashboard shows

Latest checkpoint · phase status · candidate status · eval status · epic/story status
· safety invariants · links to reports. (All from the redacted snapshot.)

## Why the dashboard is read-only

- It only **reads** a local redacted snapshot and renders it via `textContent`
  (no `innerHTML`, no dynamic code execution).
- **No action surface:** no button, no form, no `onclick`, no POST.
- **No external network:** the smoke gate asserts every request is `127.0.0.1`
  (no CDN / external fetch / API call).
- **No secret display:** the snapshot is generated from redacted docs and refused on
  secret detection.

## Why the dashboard cannot trigger repair / promotion / shell / API

By design there is no path from the UI to an action. Any real action (run an eval,
approve a repair, promote a candidate) is a **human terminal step** through the
existing approval-gated scripts with their human-approval markers — never from the
page. Browser/page content is untrusted and can never become a tool, repair, or
promotion trigger (CLI + Browser isolation, ADR-003).
