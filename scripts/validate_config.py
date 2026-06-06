"""Validate harness config files (no secrets, no env reads, no API calls).

Checks `config/config.example.json` (and `config/config.json` if present):
  - no suspected secret value anywhere in the file,
  - provider is fake|openai|anthropic and api_key_env is consistent (a NAME, not a
    value; null for fake),
  - allow_real_api_calls=true requires provider!=fake, api_key_env!=null,
    redact_secrets=true, fail_closed=true.

It never reads environment-variable values and never makes an API call.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE = "config/config.example.json"
LOCAL = "config/config.json"

PROVIDERS = {"fake", "openai", "anthropic"}
PROVIDER_ENV = {"fake": None, "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _key_patterns():
    spec = importlib.util.spec_from_file_location(
        "csh_val", ROOT / "scripts" / "check_secret_hygiene.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.KEY_PATTERNS


def validate_config_obj(cfg: dict, label: str) -> list[str]:
    errors: list[str] = []

    # No secret value anywhere in the serialized config.
    text = json.dumps(cfg, ensure_ascii=False)
    for risk, rx in _key_patterns().items():
        if rx.search(text):
            errors.append(f"{label}: contains a suspected secret value ({risk})")

    llm = cfg.get("llm")
    if not isinstance(llm, dict):
        errors.append(f"{label}: missing 'llm' object")
        return errors

    provider = llm.get("provider")
    if provider not in PROVIDERS:
        errors.append(f"{label}: llm.provider must be one of {sorted(PROVIDERS)} (got {provider!r})")

    api_key_env = llm.get("api_key_env")
    if api_key_env is not None:
        if not isinstance(api_key_env, str) or not ENV_NAME_RE.match(api_key_env):
            errors.append(f"{label}: llm.api_key_env must be an UPPER_SNAKE env var NAME or null (got {api_key_env!r})")
    if provider == "fake" and api_key_env not in (None,):
        errors.append(f"{label}: fake provider must have api_key_env=null")
    if provider in ("openai", "anthropic") and api_key_env not in (None, PROVIDER_ENV[provider]):
        errors.append(f"{label}: {provider} provider api_key_env should be {PROVIDER_ENV[provider]} (got {api_key_env!r})")

    allow_real = bool(llm.get("allow_real_api_calls"))
    if allow_real:
        if provider == "fake":
            errors.append(f"{label}: allow_real_api_calls=true is invalid with provider=fake")
        if api_key_env in (None, ""):
            errors.append(f"{label}: allow_real_api_calls=true requires a non-null api_key_env (env var NAME)")
        if llm.get("redact_secrets") is not True:
            errors.append(f"{label}: allow_real_api_calls=true requires redact_secrets=true")
        if llm.get("fail_closed") is not True:
            errors.append(f"{label}: allow_real_api_calls=true requires fail_closed=true")

    return errors


def check(root: Path) -> list[str]:
    errors: list[str] = []
    example = root / EXAMPLE
    if not example.exists():
        errors.append(f"missing {EXAMPLE}")
    else:
        try:
            errors += validate_config_obj(json.loads(example.read_text(encoding="utf-8")), EXAMPLE)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{EXAMPLE}: invalid JSON ({exc})")

    local = root / LOCAL
    if local.exists():
        try:
            errors += validate_config_obj(json.loads(local.read_text(encoding="utf-8")), LOCAL)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{LOCAL}: invalid JSON ({exc})")
    return errors


def main() -> int:
    errors = check(ROOT)
    if errors:
        print("[FAIL] config validation:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] config validation OK (no secrets; provider/api_key_env consistent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
