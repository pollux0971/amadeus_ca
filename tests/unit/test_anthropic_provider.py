import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.llm.anthropic_provider import AnthropicProvider
from src.llm.types import LLMMessage, LLMProviderError, LLMRequest

FAKE_KEY = "sk-ant-" + "b" * 40
SRC = (ROOT / "src" / "llm" / "anthropic_provider.py").read_text(encoding="utf-8")


def _provider():
    return AnthropicProvider(model="claude-3-5-haiku-latest", api_key_env="ANTHROPIC_API_KEY")


def _mock(body: bytes, status: int = 200):
    return lambda url, data, headers, timeout: (status, body)


def test_basics_real_api_enabled():
    p = _provider()
    assert p.provider_name == "anthropic"
    assert p.real_api_enabled is True


def test_requires_api_key_env_name():
    try:
        AnthropicProvider(api_key_env="")
        assert False
    except LLMProviderError as e:
        assert "api_key_env_required" in str(e)


def test_complete_mocked_messages_request():
    p = _provider()
    os.environ["ANTHROPIC_API_KEY"] = FAKE_KEY
    try:
        p._http_post = _mock(json.dumps({
            "content": [{"type": "text", "text": "hi back"}],
            "usage": {"input_tokens": 5, "output_tokens": 2},
            "stop_reason": "end_turn",
        }).encode())
        r = p.complete(LLMRequest(messages=[LLMMessage("system", "be brief"),
                                            LLMMessage("user", "hi")]))
        assert r.text == "hi back"
        assert r.provider == "anthropic"
        assert r.usage.estimated_tokens == 7  # input+output tokens
        assert r.redacted is True
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


def test_system_message_hoisted_out_of_messages():
    # capture the payload sent to verify role=system is not inside messages
    p = _provider()
    os.environ["ANTHROPIC_API_KEY"] = FAKE_KEY
    captured = {}
    try:
        def _cap(url, data, headers, timeout):
            captured["payload"] = json.loads(data.decode())
            captured["headers"] = headers
            return (200, b'{"content":[{"type":"text","text":"ok"}]}')
        p._http_post = _cap
        p.complete(LLMRequest(messages=[LLMMessage("system", "S"), LLMMessage("user", "U")]))
        payload = captured["payload"]
        assert payload.get("system") == "S"
        assert all(m["role"] != "system" for m in payload["messages"])
        # key carried in x-api-key header (the only place)
        assert captured["headers"].get("x-api-key") == FAKE_KEY
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


def test_fail_closed_when_no_key():
    p = _provider()
    os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        p.complete(LLMRequest(messages=[LLMMessage("user", "hi")]))
        assert False
    except LLMProviderError as e:
        assert "api_key_not_set" in str(e)
        assert "ANTHROPIC_API_KEY" in str(e)


def test_key_never_appears_in_response_or_error():
    p = _provider()
    os.environ["ANTHROPIC_API_KEY"] = FAKE_KEY
    try:
        p._http_post = _mock(json.dumps({
            "content": [{"type": "text", "text": f"leak {FAKE_KEY}"}]}).encode())
        r = p.complete(LLMRequest(messages=[LLMMessage("user", "hi")]))
        assert FAKE_KEY not in r.text and "***REDACTED***" in r.text

        def _boom(url, data, headers, timeout):
            raise RuntimeError(f"boom {FAKE_KEY}")
        p._http_post = _boom
        try:
            p.complete(LLMRequest(messages=[LLMMessage("user", "hi")]))
            assert False
        except LLMProviderError as e:
            assert FAKE_KEY not in str(e)
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


def test_usage_estimated_when_api_omits_it():
    p = _provider()
    os.environ["ANTHROPIC_API_KEY"] = FAKE_KEY
    try:
        p._http_post = _mock(b'{"content":[{"type":"text","text":"abcd"}]}')
        r = p.complete(LLMRequest(messages=[LLMMessage("user", "prompt")]))
        assert r.usage.estimated_tokens >= 1
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


def test_source_uses_stdlib_only_and_env_name():
    assert "urllib" in SRC
    assert "os.environ.get(self.api_key_env)" in SRC
    # never opens a local file (no .env/password read); urlopen (network) is allowed
    assert "open(" not in SRC.replace("urlopen", "")
    assert "x-api-key" in SRC
    for pkg in ("import requests", "import httpx", "import anthropic", "import aiohttp"):
        assert pkg not in SRC, pkg


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
