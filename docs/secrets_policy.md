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

## Planner prompt / response policy

- **The planner is fake-only and plan-only.** `src/planner/` (`FakePlanner`) uses
  the offline `fake` provider; it makes no real API call, reads no env-var key,
  and **never executes a step** (see `specs/planner/planner_contract.md`).
- **Every planner prompt/response written to a trace/report/plan MUST be redacted**
  via `src/llm/redaction.py`. Rendered plans (`plan.json`, markdown summaries) and
  any `--write` output are redacted — no secret-looking value can reach a file.
- **Plan validation fails closed on secret-looking input.** `validate_plan`
  rejects any step whose inputs contain a key-like value, and never echoes the
  offending value (reports the step location only).

## Plan execution artifacts policy

- **The execution bridge is allowlisted and plan-only-validated** (see
  `specs/planner/plan_execution_bridge_contract.md`). It executes only a validated
  plan, only allowlisted skills, never a direct shell, and never an unapproved
  high-risk step.
- **Every plan execution artifact MUST be redacted.** `plan.json`,
  `plan_execution_trace.jsonl`, `plan_execution_summary.md`, `score.json`, and the
  persisted `task.yaml` go through `src/llm/redaction.py`. The free-form goal is
  redacted at the door (`scripts/execute_plan.py`) and in the orchestrator's
  planner trace events — no secret-looking value reaches `runs/`.
- **`no_secret_in_artifacts` is a graded criterion.** Planner-execution evals scan
  every text artifact in the run dir; a secret-looking value fails the eval.

## Repair proposal artifacts policy

- **Auto Repair Loop v0 is proposal-only** (see
  `specs/repair/repair_loop_contract.md`). It never applies a patch, modifies a
  stable skill / safety_gate / promotion_policy, or promotes anything.
- **The failure analyzer reads only `score.json` / `summary.md` / `trace.jsonl`**
  (metadata), never `.env`, a password file, or any secret, and redacts every text
  it keeps.
- **Every repair proposal artifact MUST be redacted.** `repair_proposal.json`,
  `repair_proposal.md`, `failure_analysis.json`, and the `approval_checklist.md`
  go through `src/llm/redaction.py`. A secret-looking value fails proposal
  validation; the offending value is never echoed.
- **The repair planner uses the `fake` provider only** — offline, no env-var key
  read, no real API call.

## Apply artifacts policy

- **Approved Patch Application v0 is workspace-only** (see
  `specs/repair/approved_patch_application_contract.md`). It never modifies a real
  target file, a stable skill, the safety gate, or the promotion policy, and it
  never promotes.
- **Every apply artifact MUST be redacted.** `apply_manifest.json`,
  `apply_report.md`, the materialized `proposed_changes/*`, and `test_results.json`
  go through `src/llm/redaction.py`. No secret-looking value reaches an apply
  workspace.
- **Apply requires explicit human approval** (the `APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY`
  marker + a named reviewer, plus `--approved`), and runs only a **fixed test
  command allowlist** — never a proposal-derived or shell command.

## Enforcement

- `python scripts/check_secret_hygiene.py` checks the gitignore rules, that no
  secret file is git-tracked, and scans tracked files for high-confidence key
  patterns — reporting **filenames + risk only, never the secret value** (exit
  code 2 if a secret is tracked). It is wired into `scripts/validate_workflows.py`.
- This policy does NOT enable any real API call. LLM planner / auto-repair are
  separate, not-yet-started phases.
