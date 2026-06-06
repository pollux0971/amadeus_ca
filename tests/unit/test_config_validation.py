import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

VAL = ROOT / "scripts" / "validate_config.py"
_spec = importlib.util.spec_from_file_location("validate_config_under_test", VAL)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

EXAMPLE = json.loads((ROOT / "config" / "config.example.json").read_text(encoding="utf-8"))
FAKE_KEY = "sk-" + "y" * 40


def _llm(**over):
    base = {"provider": "fake", "model": "", "api_key_env": None, "enabled": False,
            "allow_real_api_calls": False, "redact_secrets": True, "fail_closed": True}
    base.update(over)
    return {"llm": base}


def test_example_passes_validation():
    assert mod.validate_config_obj(EXAMPLE, "example") == []


def test_secret_looking_value_rejected():
    cfg = _llm(api_key_env="OPENAI_API_KEY")
    # inject a key value where a NAME should be
    cfg["llm"]["api_key_env"] = FAKE_KEY
    errors = mod.validate_config_obj(cfg, "leaky")
    assert any("secret" in e.lower() or "api_key_env" in e for e in errors), errors


def test_allow_real_with_null_env_rejected():
    cfg = _llm(provider="openai", api_key_env=None, enabled=True, allow_real_api_calls=True)
    errors = mod.validate_config_obj(cfg, "bad")
    assert any("api_key_env" in e for e in errors), errors


def test_fake_with_allow_real_rejected():
    cfg = _llm(provider="fake", allow_real_api_calls=True)
    errors = mod.validate_config_obj(cfg, "bad")
    assert any("fake" in e.lower() for e in errors), errors


def test_valid_real_provider_config_passes():
    cfg = _llm(provider="anthropic", api_key_env="ANTHROPIC_API_KEY", model="claude",
               enabled=True, allow_real_api_calls=True)
    assert mod.validate_config_obj(cfg, "real") == []


def test_validate_is_pure_no_env_read():
    import inspect
    # validate_config_obj takes only (cfg, label) — it cannot read env values.
    params = list(inspect.signature(mod.validate_config_obj).parameters)
    assert params == ["cfg", "label"]
    # and the module never reads an env var VALUE (no os.environ.get / os.getenv).
    src = VAL.read_text(encoding="utf-8")
    assert "os.environ" not in src and "getenv" not in src


def test_check_validates_example_and_local():
    # check() over the repo passes (example is valid; local config.json if present).
    assert mod.check(ROOT) == []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
