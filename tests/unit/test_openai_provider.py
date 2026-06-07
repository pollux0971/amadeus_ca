import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.llm.openai_provider import OpenAIProvider
from src.llm.types import LLMMessage, LLMProviderError, LLMRequest

# Synthetic key built at runtime — no key-like literal in source.
FAKE_KEY = "sk-" + "a" * 44
SRC = (ROOT / "src" / "llm" / "openai_provider.py").read_text(encoding="utf-8")


def _provider():
    return OpenAIProvider(model="gpt-4o-mini", api_key_env="OPENAI_API_KEY")


def _mock(body: bytes, status: int = 200):
    return lambda url, data, headers, timeout: (status, body)


def test_basics_real_api_enabled():
    p = _provider()
    assert p.provider_name == "openai"
    assert p.real_api_enabled is True
    assert p.max_tokens >= 1 and p.timeout > 0


def test_requires_api_key_env_name():
    try:
        OpenAIProvider(api_key_env="")
        assert False
    except LLMProviderError as e:
        assert "api_key_env_required" in str(e)


def test_complete_mocked_no_real_api():
    p = _provider()
    os.environ["OPENAI_API_KEY"] = FAKE_KEY
    try:
        p._http_post = _mock(json.dumps({
            "choices": [{"message": {"content": "hello world"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }).encode())
        r = p.complete(LLMRequest(messages=[LLMMessage("user", "hi")]))
        assert r.text == "hello world"
        assert r.provider == "openai"
        assert r.usage.estimated_tokens == 5  # from API usage
        assert r.redacted is True
    finally:
        os.environ.pop("OPENAI_API_KEY", None)


def test_fail_closed_when_no_key():
    p = _provider()
    os.environ.pop("OPENAI_API_KEY", None)
    try:
        p.complete(LLMRequest(messages=[LLMMessage("user", "hi")]))
        assert False, "should fail closed without a key"
    except LLMProviderError as e:
        assert "api_key_not_set" in str(e)
        assert "OPENAI_API_KEY" in str(e)  # the NAME is fine to surface


def test_key_never_appears_in_response_or_error():
    p = _provider()
    os.environ["OPENAI_API_KEY"] = FAKE_KEY
    try:
        # response carrying a secret-looking value must be redacted
        p._http_post = _mock(json.dumps({
            "choices": [{"message": {"content": f"leaked {FAKE_KEY}"}}],
        }).encode())
        r = p.complete(LLMRequest(messages=[LLMMessage("user", "hi")]))
        assert FAKE_KEY not in r.text
        assert "***REDACTED***" in r.text
        # an HTTP error echoing the key-ish body is redacted too
        def _boom(url, data, headers, timeout):
            raise RuntimeError(f"boom {FAKE_KEY}")
        p._http_post = _boom
        try:
            p.complete(LLMRequest(messages=[LLMMessage("user", "hi")]))
            assert False
        except LLMProviderError as e:
            assert FAKE_KEY not in str(e)
    finally:
        os.environ.pop("OPENAI_API_KEY", None)


def test_usage_estimated_when_api_omits_it():
    p = _provider()
    os.environ["OPENAI_API_KEY"] = FAKE_KEY
    try:
        p._http_post = _mock(json.dumps({"choices": [{"message": {"content": "abcd"}}]}).encode())
        r = p.complete(LLMRequest(messages=[LLMMessage("user", "prompt")]))
        assert r.usage.estimated_tokens >= 1
        assert r.usage.output_chars == len("abcd")
    finally:
        os.environ.pop("OPENAI_API_KEY", None)


def test_bad_shape_raises_clean_error():
    p = _provider()
    os.environ["OPENAI_API_KEY"] = FAKE_KEY
    try:
        p._http_post = _mock(b'{"choices": []}')
        try:
            p.complete(LLMRequest(messages=[LLMMessage("user", "hi")]))
            assert False
        except LLMProviderError as e:
            assert "unexpected_response_shape" in str(e)
    finally:
        os.environ.pop("OPENAI_API_KEY", None)


def test_source_uses_stdlib_only_and_env_name():
    # uses urllib (stdlib); reads the key ONLY from the named env var; opens no file
    # (so no .env / password file read); key only in the Authorization header.
    assert "urllib" in SRC
    assert "os.environ.get(self.api_key_env)" in SRC
    # never opens a local file (no .env/password read); urlopen (network) is allowed
    assert "open(" not in SRC.replace("urlopen", "")
    assert "Authorization" in SRC
    # no heavy third-party HTTP client
    for pkg in ("import requests", "import httpx", "import aiohttp"):
        assert pkg not in SRC, pkg


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
