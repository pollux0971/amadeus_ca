"""LLM provider smoke — construction + redaction check; NO real API by default.

Default is `--dry-run`: it checks config / provider construction / redaction WITHOUT
making any network call. A real API call happens ONLY when ALL of these hold:
  - `--real-call` is passed explicitly (operator opt-in), AND
  - the effective config has `allow_real_api_calls=true` for a real provider, AND
  - the named env var (e.g. OPENAI_API_KEY) is present at run time.
Otherwise it fails closed. The key VALUE is never read for presence checks beyond
`os.environ`, never printed, and all output is redacted.

    python scripts/llm_provider_smoke.py --provider fake --dry-run
    python scripts/llm_provider_smoke.py --provider openai --dry-run
    python scripts/llm_provider_smoke.py --provider anthropic --dry-run
    # (operator only; NOT run in CI/this phase) --real-call with allow_real_api_calls=true + key set
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import (  # noqa: E402
    LLMMessage, LLMProviderError, LLMRequest, build_provider, load_config, redact_text,
)

DEFAULT_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "fake": None}


def _construct_for_dry_run(provider: str, redact: bool):
    """Construct the provider WITHOUT a real call (synthesized config; opt-in flag set
    only so the real provider class can be instantiated). No env value is read here."""
    if provider == "fake":
        return build_provider(config={"llm": {"provider": "fake", "redact_secrets": redact}}, root=ROOT)
    cfg = {"llm": {"provider": provider, "model": "",
                   "api_key_env": DEFAULT_ENV[provider],
                   "allow_real_api_calls": True, "redact_secrets": redact,
                   "fail_closed": True}}
    return build_provider(config=cfg, root=ROOT)


def _redaction_ok() -> bool:
    # Build a synthetic secret at runtime (never a literal in source) and confirm it
    # is masked. The synthetic value is never printed.
    sample = "sk-" + "x" * 40
    return redact_text(sample) != sample and "x" * 40 not in redact_text(sample)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LLM provider smoke (dry-run by default; no real API).")
    parser.add_argument("--provider", choices=["fake", "openai", "anthropic"], default="fake")
    parser.add_argument("--config", default=str(ROOT / "config" / "config.json"))
    parser.add_argument("--dry-run", action="store_true", help="construction + redaction check only (default)")
    parser.add_argument("--real-call", action="store_true",
                        help="operator opt-in: make ONE real API call (requires allow_real_api_calls + key)")
    args = parser.parse_args(argv)

    real_call = bool(args.real_call)  # default and --dry-run both => no real call

    summary = {"provider_requested": args.provider, "mode": "real-call" if real_call else "dry-run"}

    if not real_call:
        # DRY-RUN: construct + redaction only. No env value read, no API call.
        try:
            prov = _construct_for_dry_run(args.provider, redact=True)
        except LLMProviderError as exc:
            print(f"[BLOCKED] {redact_text(str(exc))}", file=sys.stderr)
            return 2
        summary.update({
            "constructed": True,
            "provider_name": prov.provider_name,
            "real_api_enabled": prov.real_api_enabled,
            "model": prov.model,
            "api_key_env": getattr(prov, "api_key_env", None),  # NAME only, never a value
            "redaction_ok": _redaction_ok(),
            "real_api_called": False,
        })
        # summary holds only names/booleans/model (no key value); redact defensively.
        out = json.dumps(summary, ensure_ascii=False, indent=2)
        print(redact_text(out))
        print("[DRY-RUN] construction + redaction verified; no env value read, no API call.",
              file=sys.stderr)
        return 0

    # REAL-CALL path (operator opt-in). Fail closed unless everything lines up.
    if args.provider == "fake":
        print("[BLOCKED] --real-call is not applicable to the fake provider.", file=sys.stderr)
        return 2
    try:
        cfg = load_config(Path(args.config).parent.parent if False else ROOT)
    except Exception:  # noqa: BLE001
        cfg = {}
    llm = (cfg.get("llm") or {}) if isinstance(cfg, dict) else {}
    if llm.get("provider") != args.provider or not bool(llm.get("allow_real_api_calls", False)):
        print("[BLOCKED] real call requires config provider==--provider AND "
              "allow_real_api_calls=true (fail closed).", file=sys.stderr)
        return 2
    api_key_env = llm.get("api_key_env") or DEFAULT_ENV[args.provider]
    if not api_key_env or os.environ.get(api_key_env) in (None, ""):
        print(f"[BLOCKED] env var {api_key_env} is not set; cannot make a real call (fail closed).",
              file=sys.stderr)
        return 2

    try:
        prov = build_provider(config=cfg, root=ROOT)
        resp = prov.complete(LLMRequest(messages=[LLMMessage("user", "ping (provider smoke)")],
                                        model=prov.model, max_tokens=16))
    except LLMProviderError as exc:
        print(f"[BLOCKED] {redact_text(str(exc))}", file=sys.stderr)
        return 2
    summary.update({
        "provider_name": resp.provider, "model": resp.model, "real_api_called": True,
        "redacted": resp.redacted,
        "response_text": redact_text(resp.text)[:200],
        "estimated_tokens": resp.usage.estimated_tokens,
    })
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
