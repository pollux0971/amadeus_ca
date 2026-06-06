import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.llm import FakeLLMProvider, LLMMessage, LLMRequest, MARKER_INSPECT, MARKER_FULL_BROWSER

FAKE_KEY = "sk-" + "z" * 40
FAKE_SRC = (ROOT / "src" / "llm" / "fake_provider.py").read_text(encoding="utf-8")


def _req(text):
    return LLMRequest(messages=[LLMMessage(role="user", content=text)])


def test_default_response_deterministic():
    p = FakeLLMProvider()
    r1 = p.complete(_req("hello"))
    r2 = p.complete(_req("hello"))
    assert r1.text == r2.text
    assert r1.provider == "fake"
    body = json.loads(r1.text)
    assert body == {"provider": "fake", "decision": "noop", "reason": "fake provider default response"}


def test_marker_inspect_plan():
    body = json.loads(FakeLLMProvider().complete(_req("do " + MARKER_INSPECT)).text)
    assert body["decision"] == "plan"
    assert body["plan"]["required_skills"] == ["inspect_project"]


def test_marker_full_browser_plan():
    body = json.loads(FakeLLMProvider().complete(_req(MARKER_FULL_BROWSER)).text)
    assert body["decision"] == "plan"
    assert body["plan"]["browser_mode"] == "playwright"
    assert len(body["plan"]["chain"]) == 6


def test_usage_has_values():
    r = FakeLLMProvider().complete(_req("hello world"))
    assert r.usage.input_chars > 0
    assert r.usage.output_chars > 0
    assert r.usage.estimated_tokens >= 1


def test_does_not_read_env_var():
    # Source must not read env values; functionally, a key in the env must not leak.
    assert "os.environ" not in FAKE_SRC and "getenv" not in FAKE_SRC
    os.environ["OPENAI_API_KEY"] = FAKE_KEY
    try:
        r = FakeLLMProvider().complete(_req("hello"))
    finally:
        os.environ.pop("OPENAI_API_KEY", None)
    assert FAKE_KEY not in r.text


def test_does_no_network():
    for mod in ("socket", "urllib", "requests", "http.client", "httpx"):
        assert mod not in FAKE_SRC, f"fake provider must not import {mod}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
