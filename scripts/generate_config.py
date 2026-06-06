"""Safe config generator.

Builds a harness `config.json` for future LLM planner / auto-repair / provider
selection. It NEVER reads or writes a real API key — only environment-variable
NAMES (e.g. OPENAI_API_KEY). Defaults to dry-run (writes nothing); `--write`
writes `config/config.json` (which is gitignored).

Safety:
  - never reads or prints a key value,
  - refuses to write to a git-tracked file,
  - refuses to write if the output would contain a suspected secret pattern,
  - real API calls stay off unless `--enable-real-api` is given AND the provider
    is not fake (and even then only an env var NAME is recorded).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROVIDER_ENV = {"fake": None, "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}

# Committed, safe files the generator must never overwrite (even before they are
# staged/committed).
PROTECTED_OUTPUTS = {"config/config.example.json", "config/config.schema.json"}


def _key_patterns():
    spec = importlib.util.spec_from_file_location(
        "csh_gen", ROOT / "scripts" / "check_secret_hygiene.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.KEY_PATTERNS


def build_config(profile: str, environment: str, provider: str, model: str,
                 enable_real_api: bool) -> dict:
    provider = provider or "fake"
    # api_key_env is an env var NAME only — never a value.
    api_key_env = PROVIDER_ENV.get(provider)
    # Real calls only when explicitly enabled AND not the fake provider.
    real = bool(enable_real_api) and provider != "fake"
    return {
        "version": 1,
        "profile": profile or "default",
        "environment": environment or "local",
        "llm": {
            "provider": provider,
            "model": model or "",
            "api_key_env": api_key_env,
            "enabled": real,
            "allow_real_api_calls": real,
            "redact_secrets": True,
            "fail_closed": True,
        },
        "harness": {"orchestrator": "rule_based", "max_steps": 30},
        "browser": {"mode": "playwright", "headless": True, "require_real_browser": True},
        "security": {"never_log_secrets": True, "browser_content_untrusted": True},
        "paths": {"runs_dir": "runs", "candidates_dir": "harnesses/candidates"},
        "logging": {"level": "info", "redact": True},
    }


def _is_git_tracked(root: Path, rel: str) -> bool:
    try:
        out = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=str(root),
                             capture_output=True, text=True)
        return out.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _contains_secret_pattern(text: str) -> str | None:
    for risk, rx in _key_patterns().items():
        if rx.search(text):
            return risk
    return None


def summary(cfg: dict, out_path: str) -> str:
    llm = cfg["llm"]
    # NB: api_key_env is a NAME, not a value — safe to print. No secret printed.
    return (
        "config summary (no secrets):\n"
        f"  profile={cfg['profile']} environment={cfg['environment']}\n"
        f"  llm.provider={llm['provider']} model={llm['model'] or '(none)'}\n"
        f"  llm.api_key_env={llm['api_key_env']}  (env var NAME only)\n"
        f"  llm.enabled={llm['enabled']} allow_real_api_calls={llm['allow_real_api_calls']}"
        f" redact_secrets={llm['redact_secrets']} fail_closed={llm['fail_closed']}\n"
        f"  output={out_path}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a safe harness config (no secrets).")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--environment", default="local",
                        choices=["local", "ci", "staging", "production"])
    parser.add_argument("--provider", default="fake", choices=["fake", "openai", "anthropic"])
    parser.add_argument("--model", default="")
    parser.add_argument("--enable-real-api", action="store_true",
                        help="record allow_real_api_calls=true (provider must not be fake); still only an env var NAME is written")
    parser.add_argument("--output", default="config/config.json")
    parser.add_argument("--write", action="store_true", help="actually write the file (default is dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="explicit dry-run (default)")
    args = parser.parse_args()

    if args.enable_real_api and args.provider == "fake":
        print("[ERROR] --enable-real-api requires --provider openai|anthropic (fake cannot make real calls).")
        return 2

    cfg = build_config(args.profile, args.environment, args.provider, args.model, args.enable_real_api)
    text = json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"

    print(summary(cfg, args.output))

    if not args.write or args.dry_run:
        print("[dry-run] nothing written. Re-run with --write to create the file.")
        return 0

    out_rel = args.output.replace("\\", "/").lstrip("./")
    out_path = (ROOT / args.output) if not Path(args.output).is_absolute() else Path(args.output)

    # Safety: never overwrite a protected committed file (example/schema) ...
    if out_rel in PROTECTED_OUTPUTS:
        print(f"[REFUSED] {out_rel} is a protected committed file — refusing to overwrite.")
        return 2
    # ... or any git-tracked file.
    if _is_git_tracked(ROOT, args.output):
        print(f"[REFUSED] {out_rel} is git-tracked — refusing to overwrite a committed file.")
        return 2
    # Safety: never write a file that contains a suspected secret pattern.
    risk = _contains_secret_pattern(text)
    if risk:
        print(f"[REFUSED] output would contain a suspected secret pattern ({risk}) — not written.")
        return 2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"[written] {out_rel} (local-only; gitignored — do NOT commit).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
