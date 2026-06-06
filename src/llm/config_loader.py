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
        # Even when allowed, real providers are intentionally NOT implemented in
        # this phase. No env var value is read; no API call is made.
        raise LLMProviderError(
            f"real_provider_not_implemented: {provider} "
            "(fake provider only; real providers require a future, operator-gated phase)"
        )

    raise LLMProviderError(f"unknown_provider: {provider!r} (expected fake|openai|anthropic)")
