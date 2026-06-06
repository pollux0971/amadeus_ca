"""LLM smoke — fake provider only by default. No real API, no secrets printed.

Loads the config, builds a provider (fake by default / forced with --fake-only),
sends one fake request, and prints a REDACTED response summary. If the config
asks for a real provider that is not allowed, it fails closed (exit 2).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.llm import (  # noqa: E402
    LLMMessage, LLMRequest, LLMProviderError, build_provider, redact_mapping, redact_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM fake smoke (no real API).")
    parser.add_argument("--fake-only", action="store_true",
                        help="force the fake provider regardless of config (default-safe)")
    parser.add_argument("--marker", default="",
                        help="optional FAKE_PLAN_* marker to exercise a canned plan")
    args = parser.parse_args()

    try:
        provider = build_provider(fake_only=args.fake_only, root=ROOT)
    except LLMProviderError as exc:
        # Fail closed — redact the reason defensively (it never contains a key).
        print(f"[BLOCKED] {redact_text(str(exc))}")
        return 2

    prompt = "harness fake smoke." + ((" " + args.marker) if args.marker else "")
    request = LLMRequest(messages=[LLMMessage(role="user", content=prompt)], model=provider.model)
    response = provider.complete(request)

    try:
        parsed = json.loads(response.text)
    except Exception:  # noqa: BLE001
        parsed = response.text

    summary = {
        "provider": response.provider,
        "model": response.model or "(none)",
        "real_api_enabled": provider.real_api_enabled,
        "redacted": response.redacted,
        "usage": {
            "input_chars": response.usage.input_chars,
            "output_chars": response.usage.output_chars,
            "estimated_tokens": response.usage.estimated_tokens,
        },
        "response": parsed,
    }
    # Redact the whole printed summary defensively (never print a secret).
    print(json.dumps(redact_mapping(summary), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
