"""FakeLLMProvider — deterministic, offline, no env reads, no secrets.

Used by default and as the fail-closed fallback. It performs NO network request
and reads NO environment variable. Responses are deterministic JSON, optionally
keyed off simple markers in the prompt (for planner/auto-repair test scaffolding).
"""
from __future__ import annotations

import json

from .provider import LLMProvider
from .redaction import redact_text
from .types import LLMRequest, LLMResponse, LLMUsage

MARKER_INSPECT = "FAKE_PLAN_INSPECT_PROJECT"
MARKER_FULL_BROWSER = "FAKE_PLAN_FULL_BROWSER_E2E"


class FakeLLMProvider(LLMProvider):
    provider_name = "fake"

    def __init__(self, model: str = "", redaction_enabled: bool = True):
        super().__init__(model=model, real_api_enabled=False, redaction_enabled=redaction_enabled)

    def complete(self, request: LLMRequest) -> LLMResponse:
        prompt = request.prompt_text

        if MARKER_INSPECT in prompt:
            payload = {
                "provider": "fake",
                "decision": "plan",
                "reason": "fake inspect_project plan",
                "plan": {"required_skills": ["inspect_project"],
                         "goal": "inspect the fixture project"},
            }
        elif MARKER_FULL_BROWSER in prompt:
            payload = {
                "provider": "fake",
                "decision": "plan",
                "reason": "fake full_browser_e2e plan summary",
                "plan": {
                    "browser_mode": "playwright",
                    "chain": [
                        "start_local_server", "open_localhost_browser",
                        "read_browser_console", "patch_file_and_run_tests",
                        "open_localhost_browser", "read_browser_console",
                    ],
                },
            }
        else:
            payload = {
                "provider": "fake",
                "decision": "noop",
                "reason": "fake provider default response",
            }

        text = json.dumps(payload, ensure_ascii=False)
        # Redaction is a no-op here (no secrets), but the pipeline always applies it.
        out_text = redact_text(text) if self.redaction_enabled else text
        usage = LLMUsage(
            input_chars=len(prompt),
            output_chars=len(out_text),
            estimated_tokens=max(1, (len(prompt) + len(out_text)) // 4),
        )
        return LLMResponse(text=out_text, provider="fake", model=self.model,
                           usage=usage, redacted=self.redaction_enabled)
