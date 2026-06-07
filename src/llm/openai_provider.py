"""OpenAIProvider — minimal, safe OpenAI chat-completions provider.

Safety invariants (see specs/llm/llm_provider_contract.md, docs/secrets_policy.md):
  - The API key is read ONLY from `os.environ[api_key_env]`, and ONLY at call time.
    Never from a file, never from `.env`, never from `password_and_api.txt`, never
    from config (config holds the env-var NAME only).
  - The key is placed only in the Authorization header; it is NEVER logged, returned,
    traced, or put in an error message.
  - Every prompt/response/error that leaves this module is redacted
    (`src/llm/redaction.py`). All errors become `LLMProviderError` with no secret.
  - No real call happens unless `complete()` is invoked (operator opt-in via config
    `allow_real_api_calls=true` + provider=openai + the env var present at run time).
  - Uses only the standard library (`urllib`); no new heavy dependency.

`_http_post` is a small seam so unit tests can mock HTTP and never hit a real API.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .provider import LLMProvider
from .redaction import redact_text
from .types import LLMProviderError, LLMRequest, LLMResponse, LLMUsage

DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TIMEOUT = 30.0


class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self, model: str = "", api_key_env: str = "OPENAI_API_KEY",
                 timeout: float = DEFAULT_TIMEOUT, max_tokens: int = DEFAULT_MAX_TOKENS,
                 url: str = DEFAULT_OPENAI_URL, redaction_enabled: bool = True):
        super().__init__(model=model or DEFAULT_MODEL, real_api_enabled=True,
                         redaction_enabled=redaction_enabled)
        if not api_key_env:
            raise LLMProviderError("api_key_env_required: OpenAI provider needs an env var NAME")
        self.api_key_env = api_key_env
        self.timeout = float(timeout)
        self.max_tokens = int(max_tokens) if max_tokens else DEFAULT_MAX_TOKENS
        self.url = url

    # -- HTTP seam (mocked in unit tests; never hits a real API in tests/dry-run) --
    def _http_post(self, url: str, data: bytes, headers: dict, timeout: float):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed URL)
            return resp.status, resp.read()

    def _redact(self, text: str) -> str:
        return redact_text(text) if self.redaction_enabled else text

    def complete(self, request: LLMRequest) -> LLMResponse:
        # 1) Read the key ONLY from the named env var, ONLY now. Never logged.
        key = os.environ.get(self.api_key_env)
        if not key:
            # The NAME is safe to surface; the VALUE is never read/printed.
            raise LLMProviderError(f"api_key_not_set: env var {self.api_key_env} is not set "
                                   "(fail closed; no real call made)")

        model = request.model or self.model
        max_tokens = request.max_tokens or self.max_tokens
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {key}",   # the ONLY place the key appears
            "Content-Type": "application/json",
        }

        try:
            status, body = self._http_post(self.url, data, headers, self.timeout)
        except urllib.error.HTTPError as exc:  # noqa: BLE001
            # Read the body defensively and redact everything; never echo the key.
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                detail = ""
            raise LLMProviderError(self._redact(
                f"openai_http_error: status={getattr(exc, 'code', '?')} {detail}")[:500])
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(self._redact(f"openai_request_failed: {exc}")[:500])

        if status and int(status) >= 400:
            raise LLMProviderError(f"openai_http_status: {status}")

        try:
            parsed = json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body)
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(self._redact(f"openai_bad_response: {exc}")[:300])

        try:
            text = parsed["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise LLMProviderError("openai_unexpected_response_shape")

        out_text = self._redact(text)
        usage = _usage_from(parsed.get("usage"), request.prompt_text, out_text)
        finish = ""
        try:
            finish = str(parsed["choices"][0].get("finish_reason", ""))
        except (KeyError, IndexError, TypeError):
            finish = ""
        return LLMResponse(
            text=out_text, provider=self.provider_name, model=model, usage=usage,
            redacted=self.redaction_enabled,
            metadata={"finish_reason": self._redact(finish)},
        )


def _usage_from(api_usage, prompt: str, out_text: str) -> LLMUsage:
    """Use API token counts when present; else estimate from char counts."""
    if isinstance(api_usage, dict):
        prompt_tok = int(api_usage.get("prompt_tokens", 0) or 0)
        completion_tok = int(api_usage.get("completion_tokens", 0) or 0)
        total = int(api_usage.get("total_tokens", prompt_tok + completion_tok) or 0)
        if total:
            return LLMUsage(input_chars=len(prompt), output_chars=len(out_text),
                            estimated_tokens=total)
    return LLMUsage(input_chars=len(prompt), output_chars=len(out_text),
                    estimated_tokens=max(1, (len(prompt) + len(out_text)) // 4))
