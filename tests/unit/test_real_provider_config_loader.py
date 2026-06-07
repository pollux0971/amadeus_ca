import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.llm.config_loader import build_provider
from src.llm.fake_provider import FakeLLMProvider
from src.llm.openai_provider import OpenAIProvider
from src.llm.anthropic_provider import AnthropicProvider
from src.llm.types import LLMProviderError

LOADER_SRC = (ROOT / "src" / "llm" / "config_loader.py").read_text(encoding="utf-8")
FAKE_KEY = "sk-" + "c" * 44


def test_default_is_fake():
    p = build_provider(config={"llm": {"provider": "fake"}})
    assert isinstance(p, FakeLLMProvider)
    assert p.real_api_enabled is False


def test_fake_only_forced():
    p = build_provider(config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                                       "allow_real_api_calls": True}}, fake_only=True)
    assert isinstance(p, FakeLLMProvider)


def test_real_provider_blocked_when_not_allowed():
    for prov in ("openai", "anthropic"):
        try:
            build_provider(config={"llm": {"provider": prov, "api_key_env": "X_KEY",
                                           "allow_real_api_calls": False}})
            assert False, f"{prov} should be fail-closed"
        except LLMProviderError as e:
            assert "real_api_not_allowed" in str(e)


def test_real_provider_built_when_allowed():
    p = build_provider(config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                                       "allow_real_api_calls": True, "model": "gpt-4o-mini"}})
    assert isinstance(p, OpenAIProvider)
    assert p.real_api_enabled is True and p.api_key_env == "OPENAI_API_KEY"
    a = build_provider(config={"llm": {"provider": "anthropic", "api_key_env": "ANTHROPIC_API_KEY",
                                       "allow_real_api_calls": True}})
    assert isinstance(a, AnthropicProvider)


def test_allowed_but_missing_env_name_fails_closed():
    try:
        build_provider(config={"llm": {"provider": "openai", "allow_real_api_calls": True}})
        assert False
    except LLMProviderError as e:
        assert "api_key_env_required" in str(e)


def test_unknown_provider_fails_closed():
    try:
        build_provider(config={"llm": {"provider": "bogus"}})
        assert False
    except LLMProviderError as e:
        assert "unknown_provider" in str(e)


def test_construction_reads_no_env_value_and_makes_no_call():
    # source must not read a key VALUE or call out at construction
    assert "os.environ" not in LOADER_SRC and "getenv" not in LOADER_SRC
    assert "urlopen" not in LOADER_SRC and "password_and_api.txt" not in LOADER_SRC
    # functional: building a real provider with a key in env does NOT read/leak it
    os.environ["OPENAI_API_KEY"] = FAKE_KEY
    try:
        p = build_provider(config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                                           "allow_real_api_calls": True}})
        # provider holds the NAME, never the value
        assert p.api_key_env == "OPENAI_API_KEY"
        assert FAKE_KEY not in repr(vars(p))
    finally:
        os.environ.pop("OPENAI_API_KEY", None)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
