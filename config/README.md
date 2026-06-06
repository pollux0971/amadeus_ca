# Config

Configuration entry point for the harness (and future LLM planner / auto-repair /
provider selection). **It never stores API key values — only environment-variable
NAMES.** No real API call is enabled by anything here.

## Files

- **`config.schema.json`** — the schema (committed, tracked).
- **`config.example.json`** — a **safe** committed template (`provider: "fake"`,
  `api_key_env: null`, `enabled: false`, `allow_real_api_calls: false`).
- **`config.json`** — **local-only, generated, gitignored — do NOT commit.**

## Rules

- **API keys live only in `.env` (gitignored) or environment variables** — never
  in any config file. Config may reference an env var **name** (e.g.
  `OPENAI_API_KEY`), never a key value.
- **Default provider is `fake`.** Real API calls are off by default
  (`enabled: false`, `allow_real_api_calls: false`).
- **Real API calls require an explicit operator opt-in** (`--enable-real-api` on
  the generator, plus a real key present in the environment at run time). Nothing
  here turns them on automatically.
- A generated config must pass the secret scanner (`scripts/check_secret_hygiene.py`)
  and `scripts/validate_config.py`.

## Generate a config

```bash
# safe preview (writes nothing):
python scripts/generate_config.py --dry-run

# write a local fake-provider config/config.json (gitignored):
python scripts/generate_config.py --provider fake --write

# a real-provider config records only the env var NAME, never a key value:
python scripts/generate_config.py --provider openai --enable-real-api --write

# validate:
python scripts/validate_config.py
```

The generator: defaults to dry-run; refuses to overwrite a git-tracked file;
refuses to write if the output would contain a suspected secret pattern; and
never prints a key value. See `docs/secrets_policy.md` and
`specs/llm/llm_provider_contract.md`.
