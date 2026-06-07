# Multimodal / Data Channels — Artifact Storage Policy (planning only)

Planning only — **no runtime implementation, no new data channel implemented**. This
defines where a future channel's ingested artifacts live and how they are handled.

## Where artifacts live

- Ingested artifacts go under a **gitignored** run/workspace location (e.g.
  `runs/<id>/multimodal/` or a dedicated ingest workspace) — never committed to the
  repo, exactly like `runs/` today.
- Original binaries (images/PDFs) are kept only as long as needed and never committed
  (no `.venv`, runs, browser cache, screenshots, or any binary blob is committed).

## Handling rules

- **Redacted before trace/report.** **Multimodal artifacts must be redacted**
  (`src/llm/redaction.py`) before any extracted text reaches a trace/report; a
  secret-looking value becomes `***REDACTED***`. **No secret in artifacts.**
- **Inert storage.** Stored artifacts are data only; nothing about storage executes
  content (**no raw shell**, no eval), and storage never triggers a tool, repair, or
  promotion.
- **No protected-surface writes.** Ingestion/storage never writes a stable skill, the
  safety gate, or the promotion policy (**no stable modification**); never modifies an
  active candidate runtime.
- **No secret source.** Storage never reads `.env` key values or
  `/data/python/computer_agent_v5/password_and_api.txt`; **no real API** call is made
  to fetch or process artifacts in planning.

## Lifecycle

- **Create** → ingest into an isolated, redacted artifact under the gitignored
  location.
- **Read** → only redacted views are surfaced (consistent with the UI dashboard
  redacted-artifact model).
- **Dispose** → artifacts are scratch; deleting the run/ingest workspace fully
  removes them (no live/stable state touched).

## Verification hook (future)

Each channel's eval asserts: artifacts land only under the gitignored location, every
surfaced string is redacted (`redact_text(x) == x`), and no secret/protected-surface
write occurs.
