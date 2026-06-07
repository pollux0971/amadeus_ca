# UI Dashboard Skeleton (read-only, v0)

A **read-only** static dashboard that visualizes the harness's project status from a
**redacted snapshot** — checkpoints, phase status, candidate status, eval status,
epic/story status, safety invariants, and links to reports.

**Story:** [`../docs/epics/stories/story_ui_dashboard_v0.md`](../docs/epics/stories/story_ui_dashboard_v0.md)
(EPIC-UI). Planning docs: [`../docs/ui_dashboard/`](../docs/ui_dashboard/).

## Hard boundaries (enforced by `scripts/validate_dashboard.py`)

- **Read-only.** The dashboard only reads a local redacted snapshot and renders it.
- **No action execution.** No button runs anything; no repair / apply / merge /
  staging / promotion trigger.
- **No raw shell. No API call.** The static page makes no external network request;
  it reads only a local relative JSON file.
- **No secret display.** The snapshot is generated from redacted docs and is refused
  if any secret-looking value is present; the page renders text via `textContent`
  only (no `innerHTML`, no `eval`).
- **No browser-content-to-tool bridge.** Snapshot content is data, never an
  instruction or a tool trigger.
- **No stable modification.** The dashboard never writes the repo.

## Files

- `static/index.html` — the page shell (read-only).
- `static/app.js` — loads `data/dashboard_snapshot.json` (falls back to
  `data/dashboard_snapshot.example.json`) and renders it; no actions.
- `static/styles.css` — styling only.
- `data/dashboard_snapshot.example.json` — committed example snapshot (no secret).
- `data/dashboard_snapshot.json` — **generated** (gitignored) by
  `scripts/generate_dashboard_snapshot.py`.

## How to use

```bash
# regenerate the snapshot from redacted docs (no .env, no runs raw, no API, no shell)
python scripts/generate_dashboard_snapshot.py
# validate the skeleton + snapshot
python scripts/validate_dashboard.py
# view: open ui_dashboard/static/index.html in a browser (read-only)
```

The page is a skeleton: it visualizes status only. Any real action (run an eval,
approve a repair, promote) is performed by a human in a terminal through the
existing approval-gated scripts — never from this UI.

## Real-browser smoke gate

A read-only real-browser smoke gate verifies the dashboard loads and stays read-only
in a real Playwright browser:

```bash
python scripts/run_dashboard_smoke.py --dry-run   # safe anywhere; runs nothing
python scripts/run_dashboard_smoke.py             # only with Playwright + Chromium (.venv)
```

The gate (`evals/dashboard/ui_dashboard_readonly_smoke.yaml`) starts an **in-process**
localhost static server (no subprocess/shell), opens the dashboard, and asserts:
title / heading / latest checkpoint / phase status / eval status visible; snapshot
visible; **no button / no form / no onclick / no POST / no external request / no
secret / no action trigger**; then tears down the browser + server with **no
lingering process**. Score = 1.0. See
[`../reports/story_ui_dashboard_smoke_v0/README.md`](../reports/story_ui_dashboard_smoke_v0/README.md).
