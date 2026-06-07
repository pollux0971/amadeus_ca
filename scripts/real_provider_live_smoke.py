"""Real provider live smoke — minimal, fail-closed, operator-opt-in OpenAI check.

This script proves that the OpenAI real provider can complete ONE minimal real API
call, while keeping every hard safety boundary from `docs/secrets_policy.md` and
`specs/llm/llm_provider_contract.md`:

  - **Dry-run is the default.** Without `--real-call` NOTHING hits the network — the
    script only verifies config / env-var NAME / provider construction / redaction.
  - **A real call needs explicit operator opt-in** (`--real-call`) AND the named env
    var present at run time. Otherwise it fails closed (exit 2 = BLOCKED).
  - **The key is read ONLY from the named env var, ONLY at call time** (inside the
    provider's `complete()`). Never from a file, `.env`, `config`, or
    `password_and_api.txt`. Its VALUE is never read here, never printed, never
    written to a report.
  - **Config holds the env-var NAME only**, never a key value.
  - **The prompt is FIXED** — `Reply with exactly: provider-ok` — never arbitrary.
  - **Everything that leaves this module is redacted** (`src/llm/redaction.py`):
    stdout, stderr, and `live_smoke_report.json` / `live_smoke_report.md`.
  - **OpenAI only this round.** Anthropic is intentionally BLOCKED / NOT TESTED.
  - **No planner, no plan execution, no auto-repair, no stable promotion** — this is
    a single provider call and nothing else.

Exit codes:
  0  success — dry-run verified, OR a real call completed and the expectation was met
  1  failure — a real call was made but errored, or the expectation was not met
  2  blocked — fail-closed (env var missing, provider not supported this round, …)

Usage:
    python scripts/real_provider_live_smoke.py --provider openai --dry-run
    python scripts/real_provider_live_smoke.py --provider openai --real-call --expect provider-ok
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import (  # noqa: E402
    LLMMessage, LLMProviderError, LLMRequest, OpenAIProvider, load_config, redact_text,
)

# Fixed, minimal smoke prompt — never an arbitrary prompt (policy).
FIXED_SMOKE_PROMPT = "Reply with exactly: provider-ok"
DEFAULT_EXPECT = "provider-ok"
# Keep the response tiny — no long output from a smoke test.
SMOKE_MAX_TOKENS = 16

# Env-var NAME per provider (a NAME, never a value).
PROVIDER_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
# Only OpenAI is exercised this round; Anthropic stays blocked / not tested.
SUPPORTED_REAL_PROVIDERS = {"openai"}

ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

DEFAULT_OUT_DIR = ROOT / "runs" / "real_provider_live_smoke"


def _redact(text: str) -> str:
    return redact_text(text if isinstance(text, str) else str(text))


def _redaction_ok() -> bool:
    """Confirm redaction masks a synthetic key built at runtime (never a literal)."""
    sample = "sk-" + "z" * 44
    masked = redact_text(sample)
    return masked != sample and ("z" * 44) not in masked


def _config_has_no_secret_and_name_only(root: Path) -> tuple[bool, str]:
    """Reuse validate_config to confirm config carries no key value and api_key_env
    is a NAME (or null). Never reads an env-var value; never makes a call."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "validate_config_for_smoke", root / "scripts" / "validate_config.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    errors = mod.check(root)
    if errors:
        return False, "; ".join(errors)
    return True, "config has no secret value; api_key_env is a NAME only"


def _write_reports(out_dir: Path, summary: dict) -> tuple[Path, Path]:
    """Write redacted JSON + MD reports. No secret can reach either file."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # Defensive: redact every string in the structure before writing.
    safe = json.loads(redact_text(json.dumps(summary, ensure_ascii=False)))
    json_path = out_dir / "live_smoke_report.json"
    md_path = out_dir / "live_smoke_report.md"
    json_path.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    md_path.write_text(_render_md(safe), encoding="utf-8")
    return json_path, md_path


def _render_md(s: dict) -> str:
    lines = [
        "# Real Provider Live Smoke Report",
        "",
        f"- generated_at: {s.get('generated_at', '')}",
        f"- provider_requested: {s.get('provider_requested', '')}",
        f"- mode: {s.get('mode', '')}",
        f"- status: {s.get('status', '')}",
        f"- api_key_env: {s.get('api_key_env', '')}  (NAME only — never a value)",
        f"- real_api_called: {s.get('real_api_called', False)}",
        f"- redaction_ok: {s.get('redaction_ok', '')}",
    ]
    if "model" in s:
        lines.append(f"- model: {s.get('model', '')}")
    if "expect" in s:
        lines.append(f"- expect: {s.get('expect', '')}")
    if "expectation_met" in s:
        lines.append(f"- expectation_met: {s.get('expectation_met', '')}")
    if "response_text" in s:
        lines.append(f"- response_text (redacted): {s.get('response_text', '')}")
    if "estimated_tokens" in s:
        lines.append(f"- estimated_tokens: {s.get('estimated_tokens', '')}")
    if "failure_reason" in s:
        lines.append(f"- failure_reason (redacted): {s.get('failure_reason', '')}")
    lines += [
        "",
        "> No secret is present in this report. The API key is read only from the "
        "named environment variable at call time and is never written here.",
        "",
    ]
    return "\n".join(lines)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _emit(summary: dict, out_dir: Path) -> None:
    """Print a redacted summary to stdout and persist redacted reports."""
    out = json.dumps(summary, ensure_ascii=False, indent=2)
    print(redact_text(out))
    json_path, md_path = _write_reports(out_dir, summary)
    print(f"[REPORT] {json_path}", file=sys.stderr)
    print(f"[REPORT] {md_path}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Real provider live smoke (dry-run by default; OpenAI only this round).")
    parser.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    parser.add_argument("--dry-run", action="store_true",
                        help="construction + config + redaction check only (default)")
    parser.add_argument("--real-call", action="store_true",
                        help="operator opt-in: make ONE real API call (needs the env var present)")
    parser.add_argument("--expect", default=DEFAULT_EXPECT,
                        help="substring the response must contain (default: provider-ok)")
    parser.add_argument("--api-key-env", default="",
                        help="override the env-var NAME (defaults to the provider's standard name)")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR),
                        help="where to write the redacted reports (gitignored runs/ by default)")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    real_call = bool(args.real_call)  # default and --dry-run both => no real call
    provider = args.provider
    api_key_env = args.api_key_env or PROVIDER_ENV[provider]

    # Guard the env-var NAME shape (defensive; never reads its value).
    if not ENV_NAME_RE.match(api_key_env):
        print("[BLOCKED] api_key_env must be an UPPER_SNAKE env var NAME (fail closed).",
              file=sys.stderr)
        return 2

    summary: dict = {
        "generated_at": _now_iso(),
        "provider_requested": provider,
        "mode": "real-call" if real_call else "dry-run",
        "api_key_env": api_key_env,            # NAME only — never a value
        "real_api_called": False,
        "redaction_ok": _redaction_ok(),
    }

    # --------- DRY-RUN (default): verify only; never touch the network. ----------
    if not real_call:
        if provider not in PROVIDER_ENV:
            summary["status"] = "BLOCKED"
            summary["failure_reason"] = f"unknown provider {provider!r}"
            _emit(summary, out_dir)
            return 2

        cfg_ok, cfg_msg = _config_has_no_secret_and_name_only(ROOT)
        summary["config_ok"] = cfg_ok
        summary["config_note"] = _redact(cfg_msg)

        constructed = False
        construct_note = ""
        if provider == "openai":
            try:
                prov = OpenAIProvider(api_key_env=api_key_env, max_tokens=SMOKE_MAX_TOKENS,
                                      redaction_enabled=True)
                constructed = True
                summary["model"] = prov.model
                summary["provider_name"] = prov.provider_name
                summary["real_api_enabled"] = prov.real_api_enabled
            except LLMProviderError as exc:
                construct_note = _redact(str(exc))
        else:  # anthropic — not exercised this round, but construction is verifiable
            construct_note = "anthropic provider construction skipped (NOT TESTED this round)"

        summary["constructed"] = constructed
        if construct_note:
            summary["construct_note"] = construct_note
        summary["env_var_present"] = bool(os.environ.get(api_key_env))  # boolean only
        summary["fixed_prompt"] = FIXED_SMOKE_PROMPT
        summary["expect"] = args.expect

        ok = bool(summary["redaction_ok"]) and cfg_ok and (
            constructed if provider == "openai" else True)
        summary["status"] = "DRY-RUN OK" if ok else "DRY-RUN FAILED"
        _emit(summary, out_dir)
        print("[DRY-RUN] verified config / env-var NAME / construction / redaction; "
              "no env value read, no API call.", file=sys.stderr)
        return 0 if ok else 1

    # --------------- REAL-CALL path (operator opt-in). Fail closed. --------------
    # Anthropic stays blocked / not tested this round.
    if provider not in SUPPORTED_REAL_PROVIDERS:
        summary["status"] = "BLOCKED"
        summary["failure_reason"] = (
            f"real call for provider={provider} is NOT TESTED this round "
            "(OpenAI only); fail closed")
        _emit(summary, out_dir)
        print(f"[BLOCKED] {provider} real call is not supported this round (OpenAI only).",
              file=sys.stderr)
        return 2

    # The env var MUST be present; we only check presence, never read/print the value.
    if not os.environ.get(api_key_env):
        summary["status"] = "BLOCKED"
        summary["failure_reason"] = f"env var {api_key_env} is not set (fail closed; no real call)"
        _emit(summary, out_dir)
        print(f"[BLOCKED] env var {api_key_env} is not set; cannot make a real call (fail closed).",
              file=sys.stderr)
        return 2

    # Construct the OpenAI provider directly (config carries the NAME only). The key
    # is read inside complete(), only now, only from the named env var.
    try:
        prov = OpenAIProvider(api_key_env=api_key_env, max_tokens=SMOKE_MAX_TOKENS,
                              redaction_enabled=True)
        resp = prov.complete(LLMRequest(
            messages=[LLMMessage("user", FIXED_SMOKE_PROMPT)],
            model=prov.model, max_tokens=SMOKE_MAX_TOKENS))
    except LLMProviderError as exc:
        summary["status"] = "FAILED"
        summary["real_api_called"] = True
        summary["failure_reason"] = _redact(str(exc))[:500]
        _emit(summary, out_dir)
        print(f"[FAILED] {_redact(str(exc))[:300]}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - never leak a raw error/secret
        summary["status"] = "FAILED"
        summary["real_api_called"] = True
        summary["failure_reason"] = _redact(f"unexpected_error: {exc}")[:500]
        _emit(summary, out_dir)
        print("[FAILED] unexpected error (redacted).", file=sys.stderr)
        return 1

    redacted_text = _redact(resp.text)
    expect = args.expect.strip().lower()
    expectation_met = expect in redacted_text.strip().lower()

    summary.update({
        "real_api_called": True,
        "provider_name": resp.provider,
        "model": resp.model,
        "redacted": resp.redacted,
        "expect": args.expect,
        "expectation_met": expectation_met,
        "response_text": redacted_text[:200],   # redacted + truncated
        "estimated_tokens": resp.usage.estimated_tokens,
    })
    summary["status"] = "SUCCESS" if expectation_met else "FAILED"
    if not expectation_met:
        summary["failure_reason"] = (
            f"response did not contain expected {args.expect!r} (redacted text shown)")
    _emit(summary, out_dir)
    if expectation_met:
        print("[SUCCESS] real OpenAI smoke call completed; expectation met (redacted).",
              file=sys.stderr)
        return 0
    print("[FAILED] real call completed but expectation not met (redacted).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
