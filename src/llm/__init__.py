"""Minimal LLM provider abstraction (fake provider only this phase).

No real API call, no env-var value read, no secret logging. See
specs/llm/llm_provider_contract.md and docs/secrets_policy.md.
"""
from .types import LLMMessage, LLMRequest, LLMResponse, LLMUsage, LLMProviderError
from .provider import LLMProvider
from .fake_provider import FakeLLMProvider, MARKER_INSPECT, MARKER_FULL_BROWSER
from .redaction import redact_text, redact_mapping, REDACTED
from .config_loader import load_config, build_provider

__all__ = [
    "LLMMessage", "LLMRequest", "LLMResponse", "LLMUsage", "LLMProviderError",
    "LLMProvider", "FakeLLMProvider", "MARKER_INSPECT", "MARKER_FULL_BROWSER",
    "redact_text", "redact_mapping", "REDACTED", "load_config", "build_provider",
]
