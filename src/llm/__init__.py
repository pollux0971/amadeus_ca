"""LLM provider abstraction.

Fake provider is the default and the fail-closed fallback. Real providers
(OpenAI / Anthropic) exist but are only constructed when config explicitly opts in
(provider != fake AND allow_real_api_calls=true); the key is read only from the
named env var at call time and every artifact is redacted. No env-var value read at
import/construction; no real API call unless complete() is invoked under opt-in. See
specs/llm/llm_provider_contract.md and docs/secrets_policy.md.
"""
from .types import LLMMessage, LLMRequest, LLMResponse, LLMUsage, LLMProviderError
from .provider import LLMProvider
from .fake_provider import FakeLLMProvider, MARKER_INSPECT, MARKER_FULL_BROWSER
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .redaction import redact_text, redact_mapping, REDACTED
from .config_loader import load_config, build_provider

__all__ = [
    "LLMMessage", "LLMRequest", "LLMResponse", "LLMUsage", "LLMProviderError",
    "LLMProvider", "FakeLLMProvider", "OpenAIProvider", "AnthropicProvider",
    "MARKER_INSPECT", "MARKER_FULL_BROWSER",
    "redact_text", "redact_mapping", "REDACTED", "load_config", "build_provider",
]
