# Multimodal / Data Channels — Source Isolation Model (planning only)

Planning only — **no runtime implementation, no new data channel implemented**. This
defines how a future data source is isolated so its content can never act as a
control channel. **Source isolation is required** for every channel.

## Principle: data plane vs control plane

- **Data plane** — ingested bytes (a file, image, PDF, web page, external feed). This
  is **untrusted content**: it is *read*, never *executed* or *obeyed*.
- **Control plane** — the harness's own vetted code paths (skills, scripts, gates).
  Only the control plane decides what runs. Ingested content can populate a prompt or
  an artifact, but it can **never** become a tool call, a shell command, an env read,
  a repair/apply/merge/staging/promotion, or a policy change.

These planes are kept separate; there is no path by which data-plane content reaches
the control plane as an instruction (CLI + Browser isolation, ADR-003).

## Isolation requirements per source

| Source (future) | Isolation requirement |
|---|---|
| Local file | read as bytes into an isolated artifact; path/content never interpolated into a command |
| Image | decoded to a redactable artifact; never an instruction; **browser content cannot trigger tool/repair/promotion** |
| PDF | text extracted into an isolated, redacted artifact; embedded scripts/links never followed as actions |
| Web page | treated like browser content — untrusted; never converted to a tool call or a key lookup |
| External data feed | fetched into an isolated artifact; never an action trigger; its own auth (if any) via env-var name only, never a file/secret |

## Hard rules

- **One isolated artifact per ingest.** Content lands in a dedicated, redacted
  artifact (see [`artifact_storage_policy.md`](artifact_storage_policy.md)); it is not
  spliced into code, config, or a command.
- **No content-derived execution.** No `eval`/`exec`, no shell, no tool dispatch, no
  gate trigger derived from ingested content. **No raw shell.**
- **No stable modification.** Ingestion can never modify a stable skill, the safety
  gate, or the promotion policy.
- **No real API / no secret.** Planning reads no key; ingested artifacts are redacted
  and contain no secret.

## Verification hook (future)

Each channel's eval (see [`eval_plan.md`](eval_plan.md)) must assert the data/control
separation holds — e.g. a fixture whose content *tries* to issue an instruction must
be ingested as inert, redacted data and trigger **nothing**.
