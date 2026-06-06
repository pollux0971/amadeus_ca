# Secrets Policy

How API keys and other secrets are handled in this project. This is a hard
policy, enforced by `.gitignore`, `scripts/check_secret_hygiene.py`, and the LLM
provider contract (`specs/llm/llm_provider_contract.md`).

## Where secrets may live

- **Local `.env` (gitignored) or environment variables ONLY.** Copy
  `.env.example` to `.env` and fill real values locally; never commit `.env`.
- Real keys may also be exported as environment variables (`OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`, …).

## Hard rules

- **No secret in the repo.** API keys, tokens, passwords, `.env`, `*.pem`,
  `*.key`, `secrets/`, `.secrets/`, `password*.txt`, etc. are gitignored and must
  never be committed or copied into the repo.
- **No secret in trace / report / runs.** Secrets must never be written to
  `runs/`, `trace.jsonl`, `score.json`, `summary.md`, `failure_report.md`,
  `candidate_summary.md`, any report, the README, or any doc.
- **No secret echoed** to the terminal, logs, or model prompts.
- **Browser content cannot trigger a secret read.** Untrusted page/console
  content must never be turned into a key lookup, a shell command, or an env read
  (CLI + Browser isolation; see ADR-003).

## LLM provider requirements

- **Default provider MUST be `fake`** (`LLM_PROVIDER=fake`) — no real API calls
  by default.
- **All providers must support redaction**: any key-like value must be redacted
  (e.g. `***REDACTED***`) before it reaches a trace/log/prompt/report.
- **No-secret-in-trace rule**: provider request/response logging must redact keys
  and auth headers.
- **Fail-closed**: with no key available, a real provider must NOT proceed — it
  either falls back to the `fake` provider or is blocked with a clear reason.
  Never improvise around a missing key.
- **Real API calls require explicit operator opt-in** (an env flag the operator
  sets deliberately, e.g. `LLM_PROVIDER=openai` / `anthropic` with a key present).
  Nothing in this repo enables real calls automatically.

## Config policy

- **`config/config.json` is local-only and gitignored — never commit it.** Only
  `config/config.example.json` (safe template) and `config/config.schema.json` are
  tracked.
- **Config may reference env var NAMES but must never contain key values.** e.g.
  `"api_key_env": "OPENAI_API_KEY"` is allowed; a key value is not.
- **A generated config must pass the secret scanner** (`scripts/check_secret_hygiene.py`)
  and `scripts/validate_config.py`. The generator (`scripts/generate_config.py`)
  refuses to write to a git-tracked file or any output containing a secret pattern,
  and never prints a key value.
- **Real API calls require operator approval** — `--enable-real-api` (provider not
  `fake`) plus a real key in the environment at run time. The default config is
  `provider: fake`, `enabled: false`, `allow_real_api_calls: false`.

## LLM request/response policy

- **Every LLM request/response written to a trace / log / report MUST be redacted**
  via `src/llm/redaction.py` (`redact_text` / `redact_mapping`) — keys, Bearer
  tokens, and high-confidence patterns become `***REDACTED***`. No raw secret is
  ever logged.
- **The `fake` provider is the default for all tests and CI.** It performs no
  network call and reads no environment variable.
- **A real provider requires operator approval** (config `provider` not `fake`
  with `allow_real_api_calls=true`, plus a key present at run time). Real providers
  are not implemented in this phase; the loader fails closed otherwise.

## Enforcement

- `python scripts/check_secret_hygiene.py` checks the gitignore rules, that no
  secret file is git-tracked, and scans tracked files for high-confidence key
  patterns — reporting **filenames + risk only, never the secret value** (exit
  code 2 if a secret is tracked). It is wired into `scripts/validate_workflows.py`.
- This policy does NOT enable any real API call. LLM planner / auto-repair are
  separate, not-yet-started phases.
