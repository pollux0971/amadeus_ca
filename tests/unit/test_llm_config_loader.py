import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.llm.config_loader import load_config, build_provider
from src.llm.fake_provider import FakeLLMProvider
from src.llm.types import LLMProviderError

LOADER_SRC = (ROOT / "src" / "llm" / "config_loader.py").read_text(encoding="utf-8")
FAKE_KEY = "sk-" + "q" * 40


def _temp_root(with_config_json: bool, provider="fake", allow_real=False):
    d = Path(tempfile.mkdtemp())
    (d / "config").mkdir()
    example = {
        "llm": {"provider": "fake", "model": "", "api_key_env": None, "enabled": False,
                "allow_real_api_calls": False, "redact_secrets": True, "fail_closed": True}
    }
    (d / "config" / "config.example.json").write_text(json.dumps(example), encoding="utf-8")
    if with_config_json:
        local = {"llm": {"provider": provider, "model": "", "api_key_env": None,
                         "enabled": False, "allow_real_api_calls": allow_real,
                         "redact_secrets": True, "fail_closed": True}}
        (d / "config" / "config.json").write_text(json.dumps(local), encoding="utf-8")
    return d


def test_no_config_json_loads_example():
    d = _temp_root(with_config_json=False)
    try:
        cfg = load_config(d)
        assert cfg["llm"]["provider"] == "fake"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_fake_provider_built_by_default():
    d = _temp_root(with_config_json=False)
    try:
        prov = build_provider(root=d)
        assert isinstance(prov, FakeLLMProvider)
        assert prov.provider_name == "fake" and prov.real_api_enabled is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_real_provider_blocked_when_not_allowed():
    d = _temp_root(with_config_json=True, provider="openai", allow_real=False)
    try:
        try:
            build_provider(root=d)
            assert False, "should have failed closed"
        except LLMProviderError as exc:
            assert "real_api_not_allowed" in str(exc)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_real_provider_not_implemented_even_when_allowed():
    cfg = {"llm": {"provider": "anthropic", "allow_real_api_calls": True,
                   "api_key_env": "ANTHROPIC_API_KEY", "redact_secrets": True,
                   "fail_closed": True, "model": ""}}
    try:
        build_provider(config=cfg)
        assert False, "real provider must not be constructed"
    except LLMProviderError as exc:
        assert "not_implemented" in str(exc)


def test_unknown_provider_fails_closed():
    try:
        build_provider(config={"llm": {"provider": "bogus"}})
        assert False
    except LLMProviderError as exc:
        assert "unknown_provider" in str(exc)


def test_loader_does_not_read_env_value():
    # source must not read env values
    assert "os.environ" not in LOADER_SRC and "getenv" not in LOADER_SRC
    # functionally: with a key in the env, building a fake provider does not leak it
    os.environ["OPENAI_API_KEY"] = FAKE_KEY
    try:
        prov = build_provider(config={"llm": {"provider": "fake", "redact_secrets": True}})
        assert isinstance(prov, FakeLLMProvider)
    finally:
        os.environ.pop("OPENAI_API_KEY", None)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
