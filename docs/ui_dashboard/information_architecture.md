# UI Dashboard — Information Architecture (planning only)

Planning only — **no UI implemented**. This describes the views a future read-only
dashboard would offer and the on-disk artifacts each reads. Every view is
**read-only** and renders **redacted** content only (see
[`redacted_artifact_model.md`](redacted_artifact_model.md)).

## Design principles

- **Read-only.** The dashboard observes; it never mutates the repo or runs anything.
- **No action execution / no raw shell.** No view triggers a shell or a tool.
- **No promotion from UI.** Any human action (e.g. approve a repair, run an eval)
  routes through an **existing approval-gated script** (`repair_propose`,
  `repair_apply`, `repair_merge`, `staging_promote`, `run_eval`) with its
  human-approval markers — the UI only *links to instructions*, it does not call them.
- **Redacted only.** Artifacts pass through `src/llm/redaction.py` before display.

## Views / panels

| View | Purpose | Reads (on-disk, redacted) | Actions |
|---|---|---|---|
| **Overview** | Phases, latest checkpoint, what's green | `docs/quick_resume.md`, `docs/checkpoints/`, `README.md` flags | none (read-only) |
| **Phase / Checkpoint timeline** | Frozen phases 1B→6 + tags | `docs/checkpoints/checkpoint-*.md` | none |
| **Gate chain** | Repair→apply→merge→staging→stable status | `docs/candidate_status_matrix.md`, `docs/promotion_readiness_review.md` | none |
| **Evals** | Eval list + last known scores | `evals/**.yaml`, `runs/**/score.json` (redacted) | "how to run" link to `run_eval` (no execution) |
| **Candidates** | Candidate stages/versions | `harnesses/candidates/*/candidate.yaml`, candidate docs | none |
| **Runs** | Run list + single-run report | `runs/<id>/score.json`, `summary.md`, `trace.jsonl` (redacted, metadata) | none |
| **Reports** | Phase / story report packs | `reports/**/README.md` | none |
| **Repair workspaces** | Proposal/apply/merge/staging workspaces (redacted) | `harnesses/candidates/_repair_*`, `_staging_promotions/**` | "how to approve" link to the gated script (no execution) |
| **Backlog** | Epics / stories / decision matrix | `docs/epics/**` | none |

## Information hierarchy

```
Overview
├── Phase / Checkpoint timeline   (docs/checkpoints/)
├── Gate chain                    (candidate_status_matrix / promotion_readiness_review)
├── Evals ── Runs ── Reports      (evals/ + runs/ + reports/, redacted)
├── Candidates                    (harnesses/candidates/*, excluding generated _* workspaces)
├── Repair workspaces (redacted)  (_repair_* / _staging_promotions, read-only)
└── Backlog                       (docs/epics/)
```

## Explicitly NOT in the IA

- No "Promote", "Apply", "Merge", "Stage", or "Run" **button that executes** — only
  read-only views and copy-the-command instructions.
- No raw artifact view (unredacted `trace.jsonl` / secrets).
- No settings page that writes config, env, or keys.
