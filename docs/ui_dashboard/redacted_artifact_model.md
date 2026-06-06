# UI Dashboard — Redacted Artifact Model (planning only)

Planning only — **no UI implemented**. This defines how a future dashboard exposes
on-disk artifacts: **read-only and redacted**, never raw, never a secret.

## Core rule

Every artifact the dashboard reads passes through `src/llm/redaction.py`
(`redact_text` / `redact_mapping`) **before** it is rendered. High-confidence
secret patterns (API keys, Bearer tokens, etc.) become `***REDACTED***`. The
dashboard renders the redacted copy and never the raw bytes.

## What may be shown (read-only, redacted)

| Source | Exposed as | Notes |
|---|---|---|
| `runs/<id>/score.json` | run result + criteria | redacted JSON; numbers/criteria only |
| `runs/<id>/summary.md` | run summary | redacted markdown |
| `runs/<id>/trace.jsonl` | step **metadata** | redacted; step ids, skill ids, ok/fail, durations — not raw payloads |
| `reports/**` | report packs | already redacted, committed docs |
| `docs/checkpoints/**` | frozen checkpoints | committed docs |
| `harnesses/candidates/_repair_*`, `_staging_promotions/**` | workspace artifacts | redacted (manifests/reports already redacted) |
| `evals/**`, `harnesses/candidates/*/candidate.yaml` | config metadata | no secrets by policy |

## What is NEVER shown

- **Secrets / keys / `.env` values** — never read, never rendered.
- **`/data/python/computer_agent_v5/password_and_api.txt`** — never read.
- **Raw, unredacted `trace.jsonl`** payloads or any raw artifact bytes.
- **Anything outside the repo's redactable artifacts** (no host env, no process
  memory, no live shell output).

## Access model

- **Read-only filesystem access** to the artifact roots above; the dashboard has no
  write path to the repo.
- **No execution surface.** The dashboard process never spawns a shell, runs a
  script, or calls a tool. "Run this" is shown as a **copyable command** for a human
  to run in their own terminal through the existing gated scripts.
- **Redaction is mandatory and fail-safe.** If an artifact cannot be redacted/parsed,
  it is shown as "unavailable", never raw.

## Verification hooks (future)

- The dashboard's artifact reader must be covered by a test asserting
  `redact_text(rendered) == rendered` for every rendered string (no secret survives).
- `scripts/check_secret_hygiene.py` continues to guarantee no secret is committed;
  the dashboard adds a *runtime* redaction layer on top for anything it reads from
  `runs/` (which is gitignored and may contain fresh, unreviewed text).
