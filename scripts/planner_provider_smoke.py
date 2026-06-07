"""Planner provider smoke — provider-aware planner construction + a dry-run plan.

Default `--dry-run`: checks config / provider construction / planner construction /
redaction and builds ONE deterministic plan WITHOUT executing it and WITHOUT any
real API call. The fake provider is the default; a real provider (openai/anthropic)
is reported BLOCKED unless config opts in (allow_real_api_calls=true), and even when
opted-in it is HELD, not called (this script has no real-call path at all).

    python scripts/planner_provider_smoke.py --provider fake --dry-run
    python scripts/planner_provider_smoke.py --provider openai --dry-run
    python scripts/planner_provider_smoke.py --provider anthropic --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import LLMProviderError, redact_text  # noqa: E402
from src.planner.provider_planner import build_planner_from_config  # noqa: E402
from src.planner.plan_validator import validate_plan  # noqa: E402
from src.planner.plan_renderer import render_json  # noqa: E402
from src.planner.types import PlannerRequest  # noqa: E402

DEFAULT_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "fake": None}
SMOKE_MARKER = "FAKE_PLAN_FULL_BROWSER_E2E"


def _redaction_ok() -> bool:
    sample = "sk-" + "z" * 40
    return redact_text(sample) != sample


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Planner provider smoke (dry-run default; plan-only; no real API).")
    parser.add_argument("--provider", choices=["fake", "openai", "anthropic"], default="fake")
    parser.add_argument("--config", default=str(ROOT / "config" / "config.json"))
    parser.add_argument("--dry-run", action="store_true",
                        help="construction + redaction + one dry-run plan (default; no API)")
    args = parser.parse_args(argv)

    summary = {"provider_requested": args.provider, "mode": "dry-run",
               "real_api_called": False, "plan_executed": False}

    # 1) Fake is always constructible and is the default.
    fake_planner = build_planner_from_config(config={"llm": {"provider": "fake"}}, root=ROOT)
    summary["fake_default_confirmed"] = (fake_planner.provider_name == "fake"
                                         and fake_planner.real_api_enabled is False)

    # 2) For a real provider: confirm it is BLOCKED without opt-in, then construct it
    #    held (opt-in path) WITHOUT calling it.
    if args.provider == "fake":
        planner = fake_planner
        summary["provider_loaded"] = True
        summary["real_provider_blocked_without_opt_in"] = True  # n/a for fake; trivially safe
    else:
        env = DEFAULT_ENV[args.provider]
        # blocked without opt-in
        try:
            build_planner_from_config(config={"llm": {"provider": args.provider,
                                                      "api_key_env": env,
                                                      "allow_real_api_calls": False}}, root=ROOT)
            summary["real_provider_blocked_without_opt_in"] = False
        except LLMProviderError:
            summary["real_provider_blocked_without_opt_in"] = True
        # opt-in construction (held, not called)
        try:
            planner = build_planner_from_config(
                config={"llm": {"provider": args.provider, "api_key_env": env,
                                "allow_real_api_calls": True}}, root=ROOT, allow_real_call=False)
            summary["provider_loaded"] = True
        except LLMProviderError as exc:
            print(f"[BLOCKED] {redact_text(str(exc))}", file=sys.stderr)
            return 2

    # 3) Build ONE deterministic plan (no execution, no real call).
    resp = planner.plan(PlannerRequest(marker=SMOKE_MARKER))
    validation = validate_plan(resp.plan)
    plan_json = render_json(resp.plan, validation)

    summary.update({
        "planner": getattr(planner, "planner_name", "provider_backed"),
        "provider_name": planner.provider_name,
        "real_api_enabled": planner.real_api_enabled,
        "plan_created": bool(resp.plan.steps),
        "plan_valid": validation.valid,
        "redaction_ok": _redaction_ok(),
        "no_secret_in_plan": redact_text(plan_json) == plan_json,
    })
    out = json.dumps(summary, ensure_ascii=False, indent=2)
    print(redact_text(out))  # defensive; summary has no key value
    print("[DRY-RUN] planner+provider constructed; one plan built; not executed; no real API.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
