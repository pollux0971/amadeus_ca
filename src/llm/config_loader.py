"""Load harness config and build an LLM provider — fail-closed, no env reads.

- Loads `config/config.json` if present, else `config/config.example.json`.
- `provider=fake` -> FakeLLMProvider (default).
- A real provider (openai/anthropic) with `allow_real_api_calls=false` is BLOCKED
  (fail-closed) — it raises LLMProviderError and is never constructed.
- A real provider is NOT implemented in this phase; even when allowed it raises a
  clear "not implemented" error. No environment-variable VALUE is ever read here,
  and no API call is made.
"""
from __future__ import annotations

import json
from pathlib import Path

from .fake_provider import FakeLLMProvider
from .provider import LLMProvider
from .types import LLMProviderError

ROOT = Path(__file__).resolve().parents[2]
REAL_PROVIDERS = {"openai", "anthropic"}


def load_config(root: Path | str = ROOT) -> dict:
    root = Path(root)
    local = root / "config" / "config.json"
    example = root / "config" / "config.example.json"
    path = local if local.exists() else example
    return json.loads(path.read_text(encoding="utf-8"))


def build_provider(config: dict | None = None, root: Path | str = ROOT,
                   fake_only: bool = False) -> LLMProvider:
    cfg = config if config is not None else load_config(root)
    llm = cfg.get("llm", {}) if isinstance(cfg, dict) else {}
    redact = bool(llm.get("redact_secrets", True))
    provider = "fake" if fake_only else llm.get("provider", "fake")

    if provider == "fake":
        return FakeLLMProvider(model=llm.get("model", ""), redaction_enabled=redact)

    if provider in REAL_PROVIDERS:
        # Fail-closed: do NOT construct a real provider unless explicitly allowed.
        if not bool(llm.get("allow_real_api_calls", False)):
            raise LLMProviderError(
                f"real_api_not_allowed: provider={provider} but "
                "allow_real_api_calls=false (fail-closed; using fake is required)"
            )
        # Config stores the env var NAME only (never a key value). No env-var VALUE
        # is read here and NO API call is made at construction; the key is read only
        # at call time inside the provider's complete().
        api_key_env = llm.get("api_key_env")
        if not api_key_env or not isinstance(api_key_env, str):
            raise LLMProviderError(
                f"api_key_env_required: provider={provider} with allow_real_api_calls=true "
                "needs llm.api_key_env (an env var NAME, e.g. OPENAI_API_KEY)"
            )
        model = llm.get("model", "")
        timeout = float(llm.get("timeout_sec", 30) or 30)
        max_tokens = int(llm.get("max_tokens", 512) or 512)
        if provider == "openai":
            from .openai_provider import OpenAIProvider
            return OpenAIProvider(model=model, api_key_env=api_key_env, timeout=timeout,
                                  max_tokens=max_tokens, redaction_enabled=redact)
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(model=model, api_key_env=api_key_env, timeout=timeout,
                                 max_tokens=max_tokens, redaction_enabled=redact)

    raise LLMProviderError(f"unknown_provider: {provider!r} (expected fake|openai|anthropic)")
