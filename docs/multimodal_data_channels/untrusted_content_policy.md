# Multimodal / Data Channels — Untrusted Content Policy (planning only)

Planning only — **no runtime implementation, no new data channel implemented**. This
is the hard policy for any content a future channel ingests.

## Core rule

**Untrusted content is data, not instruction.** Anything ingested from a file, image,
PDF, web page, or external feed is treated as inert data. It is never interpreted as
a command, prompt-injection directive, tool request, or policy change.

## What untrusted content may NEVER do

- **Trigger a tool / repair / promotion.** Browser/page/file content cannot start a
  tool call, a repair proposal/apply, a candidate merge, a staging or stable
  promotion. **Browser content cannot trigger tool / repair / promotion.**
- **Become a shell or eval.** No ingested text becomes a raw shell / direct command
  (**no raw shell**), `eval`, or `exec`.
- **Read or reveal secrets.** It can never cause a `.env`/key read or a read of
  `/data/python/computer_agent_v5/password_and_api.txt`; **no secret in artifacts**.
- **Modify protected surfaces.** It can never modify a stable skill, the safety gate,
  or the promotion policy (**no stable modification**).
- **Reach a real API.** Planning makes **no real API** call; ingestion never opts in
  to one.

## Prompt-injection handling

- Ingested content that *looks like* an instruction ("ignore previous instructions",
  "run this", "promote now") is still **data**. It is quoted/escaped into an artifact
  and never elevated to a control signal.
- The harness's control plane decides actions from its own vetted code, never from
  ingested content (data/control separation —
  [`source_isolation_model.md`](source_isolation_model.md)).

## Redaction

- **Multimodal artifacts must be redacted** (`src/llm/redaction.py`) before they reach
  a trace/report. A secret-looking value in ingested content becomes `***REDACTED***`.

## Verification hook (future)

Each channel's eval includes an **adversarial fixture**: content crafted to attempt
an instruction/tool/promotion trigger. The eval passes only if the attempt results in
inert, redacted data and **no** tool/repair/promotion/shell/secret access occurs.
