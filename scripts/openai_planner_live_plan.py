"""OpenAI planner live plan-only — generate ONE real plan, validate it, never run it.

This script lets the OpenAI provider produce a single, real planner *plan* from a
goal, then validates it with `PlanValidator`. It is **plan-only**: it NEVER executes
a step, NEVER starts repair / apply / merge / staging / promotion, and NEVER
auto-fixes an invalid plan — an invalid or non-JSON result produces a *blocked
report*.

Hard safety boundaries (see specs/llm/llm_provider_contract.md,
specs/planner/planner_contract.md, docs/secrets_policy.md):
  - **Fake provider stays the default everywhere else.** This script is the explicit
    opt-in surface for ONE real OpenAI plan.
  - **Dry-run by default.** Without `--real-call` NOTHING hits the network — it only
    checks config / provider construction / redaction / the plan schema.
  - **A real call requires `--real-call` + provider=openai + allow_real_api_calls=true
    + OPENAI_API_KEY present at run time.** Otherwise it fails closed (exit 2).
  - **The key is read ONLY from `os.environ['OPENAI_API_KEY']` at call time** (inside
    the provider). Never from a file, `.env`, `config`, or `password_and_api.txt`;
    never printed, traced, or written to a report. Config holds the env-var NAME only.
  - **Only a fixed system instruction + the goal** are sent — never file content,
    browser/page content, or raw run traces. A secret-looking goal is refused.
  - **Every artifact is redacted** (`plan.json`, `plan_summary.md`,
    `planner_live_report.json`, any blocked report).

Exit codes:
  0  dry-run verified, OR a real call produced a VALID plan
  1  blocked — a real call was made but the output was non-JSON or the plan was invalid
  2  fail-closed — not opted in / OPENAI_API_KEY missing / provider gate failed

Usage:
    .venv/bin/python scripts/openai_planner_live_plan.py --goal "<goal>" --dry-run
    .venv/bin/python scripts/openai_planner_live_plan.py --goal "<goal>" --real-call
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import LLMProviderError, redact_text  # noqa: E402
from src.planner.plan_renderer import render_json, render_markdown  # noqa: E402
from src.planner.plan_validator import validate_plan  # noqa: E402
from src.planner.provider_planner import (  # noqa: E402
    LIVE_PLAN_SYSTEM_PROMPT, LivePlanError, build_planner_from_config, parse_plan_from_text,
)
from src.planner.types import PlannerRequest  # noqa: E402

PROVIDER = "openai"
API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_GOAL = "Create a safe read-only project status inspection plan. Do not execute anything."
DEFAULT_OUTPUT = ROOT / "runs" / "openai_planner_live_plan"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _redaction_ok() -> bool:
    sample = "sk-" + "z" * 44
    masked = redact_text(sample)
    return masked != sample and ("z" * 44) not in masked


def _schema_self_check() -> bool:
    """Parse a minimal canonical plan and confirm it validates — proves the schema
    path works WITHOUT any network call."""
    sample = json.dumps({"goal": "self-check", "steps": [{
        "id": "inspect", "skill": "inspect_project", "inputs": {},
        "expected_outputs": ["status"], "success_criteria": ["project_inspected"],
        "risk_level": "low", "requires_approval": False, "depends_on": []}]})
    try:
        plan = parse_plan_from_text(sample, "self-check")
        return validate_plan(plan).valid
    except LivePlanError:
        return False


def _write(out_dir: Path, name: str, text: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    # Defensive: redact every artifact before it is written.
    path.write_text(redact_text(text), encoding="utf-8")
    return path


def _report(out_dir: Path, summary: dict) -> Path:
    safe = json.loads(redact_text(json.dumps(summary, ensure_ascii=False)))
    return _write(out_dir, "planner_live_report.json",
                  json.dumps(safe, ensure_ascii=False, indent=2) + "\n")


def _print_summary(summary: dict) -> None:
    print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))


def _real_config() -> dict:
    # Config carries the env-var NAME only — never a key value.
    return {"llm": {"provider": PROVIDER, "model": "", "api_key_env": API_KEY_ENV,
                    "allow_real_api_calls": True, "redact_secrets": True,
                    "fail_closed": True}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="OpenAI planner live plan-only (dry-run default; plan-only; no execution).")
    parser.add_argument("--goal", default=DEFAULT_GOAL, help="planning goal (plain text only)")
    parser.add_argument("--dry-run", action="store_true",
                        help="config / provider / redaction / schema check only (default; no API)")
    parser.add_argument("--real-call", action="store_true",
                        help="operator opt-in: make ONE real OpenAI plan generation")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="directory for redacted artifacts (gitignored runs/ by default)")
    args = parser.parse_args(argv)

    out_dir = Path(args.output)
    real_call = bool(args.real_call)
    goal = (args.goal or "").strip()

    summary: dict = {
        "generated_at": _now_iso(),
        "provider": PROVIDER,
        "api_key_env": API_KEY_ENV,           # NAME only — never a value
        "mode": "real-call" if real_call else "dry-run",
        "goal": redact_text(goal),            # redacted defensively
        "real_api_called": False,
        "plan_executed": False,               # plan-only, always
        "auto_repair": False,                 # never
        "redaction_ok": _redaction_ok(),
        "schema_ok": _schema_self_check(),
    }

    # ----------------------------- DRY-RUN (default) ----------------------------
    if not real_call:
        # Construct the planner HELD (opt-in config, but allow_real_call=False) so we
        # verify construction + fail-closed without ever calling the provider.
        blocked_without_opt_in = False
        try:
            build_planner_from_config(
                config={"llm": {"provider": PROVIDER, "api_key_env": API_KEY_ENV,
                                "allow_real_api_calls": False}}, root=ROOT)
        except LLMProviderError:
            blocked_without_opt_in = True
        try:
            held = build_planner_from_config(_real_config(), root=ROOT, allow_real_call=False)
        except LLMProviderError as exc:
            summary["status"] = "BLOCKED"
            summary["reason"] = redact_text(str(exc))
            _print_summary(summary)
            _report(out_dir, summary)
            return 2

        summary.update({
            "provider_name": held.provider_name,
            "real_api_enabled": held.real_api_enabled,
            "real_provider_blocked_without_opt_in": blocked_without_opt_in,
            "system_prompt_fixed": "read-only" in LIVE_PLAN_SYSTEM_PROMPT.lower(),
            "env_var_present": bool(os.environ.get(API_KEY_ENV)),   # boolean only
            "status": "DRY-RUN OK" if (summary["redaction_ok"] and summary["schema_ok"]
                                       and blocked_without_opt_in and held.real_api_enabled)
                      else "DRY-RUN FAILED",
        })
        _print_summary(summary)
        rpt = _report(out_dir, summary)
        print(f"[REPORT] {rpt}", file=sys.stderr)
        print("[DRY-RUN] config / provider / redaction / schema verified; "
              "no env value read, no API call, plan not generated.", file=sys.stderr)
        return 0 if summary["status"] == "DRY-RUN OK" else 1

    # ------------------------- REAL-CALL (operator opt-in) ----------------------
    if not goal:
        summary["status"] = "BLOCKED"
        summary["reason"] = "empty goal (nothing to plan); fail closed"
        _print_summary(summary)
        _report(out_dir, summary)
        print("[BLOCKED] empty goal.", file=sys.stderr)
        return 2

    # Fail closed unless the key is present (presence only; value never read here).
    if not os.environ.get(API_KEY_ENV):
        summary["status"] = "BLOCKED"
        summary["reason"] = f"env var {API_KEY_ENV} is not set (fail closed; no real call)"
        _print_summary(summary)
        _report(out_dir, summary)
        print(f"[BLOCKED] env var {API_KEY_ENV} is not set; cannot make a real call.",
              file=sys.stderr)
        return 2

    # Build the planner with opt-in for ONE real call.
    try:
        planner = build_planner_from_config(_real_config(), root=ROOT, allow_real_call=True)
    except LLMProviderError as exc:
        summary["status"] = "BLOCKED"
        summary["reason"] = redact_text(str(exc))
        _print_summary(summary)
        _report(out_dir, summary)
        print(f"[BLOCKED] {redact_text(str(exc))}", file=sys.stderr)
        return 2

    summary["provider_name"] = planner.provider_name
    summary["model"] = getattr(planner.provider, "model", "")

    # ONE real plan generation. Any provider error / non-JSON -> blocked report.
    try:
        resp = planner.live_plan(PlannerRequest(goal=goal))
        summary["real_api_called"] = True
    except LivePlanError as exc:
        summary["real_api_called"] = True  # the call may have happened; output unusable
        summary["status"] = "BLOCKED"
        summary["reason"] = redact_text(str(exc))[:400]
        _print_summary(summary)
        _write(out_dir, "blocked_report.md",
               f"# Live Plan BLOCKED\n\n- reason: {redact_text(str(exc))[:400]}\n\n"
               "> The model output could not be parsed into a plan. No plan was "
               "executed; no auto-repair was attempted.\n")
        _report(out_dir, summary)
        print(f"[BLOCKED] {redact_text(str(exc))[:300]}", file=sys.stderr)
        return 1
    except LLMProviderError as exc:
        summary["real_api_called"] = True
        summary["status"] = "BLOCKED"
        summary["reason"] = redact_text(str(exc))[:400]
        _print_summary(summary)
        _report(out_dir, summary)
        print(f"[BLOCKED] provider error (redacted).", file=sys.stderr)
        return 1

    # Validate the model's plan. An invalid plan is BLOCKED — never auto-fixed.
    validation = validate_plan(resp.plan)
    plan_json = render_json(resp.plan, validation)
    summary.update({
        "plan_valid": validation.valid,
        "plan_steps": len(resp.plan.steps),
        "plan_skills": resp.plan.skills,
        "no_secret_in_plan": redact_text(plan_json) == plan_json,
        "raw_response_redacted": resp.raw_response_redacted[:300],
        "notes": resp.notes,
    })

    if not validation.valid:
        summary["status"] = "BLOCKED"
        summary["validation_errors"] = [redact_text(e) for e in validation.errors]
        _print_summary(summary)
        _write(out_dir, "blocked_report.md", render_markdown(resp.plan, validation))
        _report(out_dir, summary)
        print("[BLOCKED] the generated plan failed validation (no auto-repair).",
              file=sys.stderr)
        return 1

    # SUCCESS: write the redacted plan artifacts.
    summary["status"] = "SUCCESS"
    _write(out_dir, "plan.json", plan_json)
    _write(out_dir, "plan_summary.md", render_markdown(resp.plan, validation))
    rpt = _report(out_dir, summary)
    _print_summary(summary)
    print(f"[REPORT] {rpt}", file=sys.stderr)
    print("[SUCCESS] one real OpenAI plan generated and validated; not executed; "
          "no auto-repair. Artifacts are redacted.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
