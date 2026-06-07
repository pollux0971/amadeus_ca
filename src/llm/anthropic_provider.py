"""AnthropicProvider — minimal, safe Anthropic Messages provider.

Same safety invariants as OpenAIProvider (see specs/llm/llm_provider_contract.md,
docs/secrets_policy.md):
  - Key read ONLY from `os.environ[api_key_env]`, ONLY at call time; never from a
    file/.env/password_and_api.txt/config (config holds the env-var NAME only).
  - Key appears only in the `x-api-key` header; never logged/returned/traced/in an
    error.
  - Every prompt/response/error is redacted; all errors become `LLMProviderError`
    with no secret. Standard library (`urllib`) only.
  - No real call unless `complete()` is invoked under operator opt-in.

`_http_post` is the mock seam for unit tests (no real API in tests/dry-run).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .provider import LLMProvider
from .redaction import redact_text
from .types import LLMProviderError, LLMRequest, LLMResponse, LLMUsage

DEFAULT_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-3-5-haiku-latest"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TIMEOUT = 30.0
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"

    def __init__(self, model: str = "", api_key_env: str = "ANTHROPIC_API_KEY",
                 timeout: float = DEFAULT_TIMEOUT, max_tokens: int = DEFAULT_MAX_TOKENS,
                 url: str = DEFAULT_ANTHROPIC_URL, redaction_enabled: bool = True):
        super().__init__(model=model or DEFAULT_MODEL, real_api_enabled=True,
                         redaction_enabled=redaction_enabled)
        if not api_key_env:
            raise LLMProviderError("api_key_env_required: Anthropic provider needs an env var NAME")
        self.api_key_env = api_key_env
        self.timeout = float(timeout)
        self.max_tokens = int(max_tokens) if max_tokens else DEFAULT_MAX_TOKENS
        self.url = url

    def _http_post(self, url: str, data: bytes, headers: dict, timeout: float):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed URL)
            return resp.status, resp.read()

    def _redact(self, text: str) -> str:
        return redact_text(text) if self.redaction_enabled else text

    def complete(self, request: LLMRequest) -> LLMResponse:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise LLMProviderError(f"api_key_not_set: env var {self.api_key_env} is not set "
                                   "(fail closed; no real call made)")

        model = request.model or self.model
        max_tokens = request.max_tokens or self.max_tokens

        # Anthropic disallows role=system inside messages; hoist system text out.
        system_parts = [m.content for m in request.messages if m.role == "system"]
        messages = [{"role": m.role, "content": m.content}
                    for m in request.messages if m.role != "system"]
        payload = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if system_parts:
            payload["system"] = "\n".join(system_parts)

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "x-api-key": key,                    # the ONLY place the key appears
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

        try:
            status, body = self._http_post(self.url, data, headers, self.timeout)
        except urllib.error.HTTPError as exc:  # noqa: BLE001
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                detail = ""
            raise LLMProviderError(self._redact(
                f"anthropic_http_error: status={getattr(exc, 'code', '?')} {detail}")[:500])
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(self._redact(f"anthropic_request_failed: {exc}")[:500])

        if status and int(status) >= 400:
            raise LLMProviderError(f"anthropic_http_status: {status}")

        try:
            parsed = json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body)
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(self._redact(f"anthropic_bad_response: {exc}")[:300])

        text = _extract_text(parsed)
        if text is None:
            raise LLMProviderError("anthropic_unexpected_response_shape")

        out_text = self._redact(text)
        usage = _usage_from(parsed.get("usage"), request.prompt_text, out_text)
        return LLMResponse(
            text=out_text, provider=self.provider_name, model=model, usage=usage,
            redacted=self.redaction_enabled,
            metadata={"stop_reason": self._redact(str(parsed.get("stop_reason", "")))},
        )


def _extract_text(parsed) -> str | None:
    try:
        blocks = parsed.get("content", [])
        parts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
        if parts:
            return "".join(parts)
        # fall back to any text block
        parts = [b.get("text", "") for b in blocks if isinstance(b, dict) and "text" in b]
        return "".join(parts) if parts else None
    except (AttributeError, TypeError):
        return None


def _usage_from(api_usage, prompt: str, out_text: str) -> LLMUsage:
    if isinstance(api_usage, dict):
        in_tok = int(api_usage.get("input_tokens", 0) or 0)
        out_tok = int(api_usage.get("output_tokens", 0) or 0)
        if in_tok or out_tok:
            return LLMUsage(input_chars=len(prompt), output_chars=len(out_text),
                            estimated_tokens=in_tok + out_tok)
    return LLMUsage(input_chars=len(prompt), output_chars=len(out_text),
                    estimated_tokens=max(1, (len(prompt) + len(out_text)) // 4))
