"""OpenAI Plan Review Package v0 — turn a plan into a human-review package, NEVER run it.

This builds a *review package* from a planner plan (an OpenAI live plan, an existing
`plan.json`, or — by default — a deterministic offline fake plan). It NEVER executes a
step, NEVER auto-repairs, and NEVER starts repair / apply / merge / staging /
promotion. The package is for a human reviewer to read and (separately) approve.

The package (all artifacts redacted):
  - plan.json                  the validated, redacted plan
  - plan_summary.md            a redacted human summary
  - risk_assessment.md         per-step + overall risk; BLOCKED if any step is not
                               low-risk OR uses a non-allowlisted (read-only) skill
  - approval_checklist.md      NOT APPROVED BY DEFAULT / PLAN NOT EXECUTED / HUMAN
                               APPROVAL REQUIRED, with APPROVED_FOR_READONLY_EXECUTION: false
  - execution_preconditions.md the conditions any later read-only execution must meet
  - review_report.json         machine summary (status, validity, blocked reasons)

Safety:
  - Fake provider is the default; a real OpenAI plan needs `--real-call` (one call) +
    provider=openai + allow_real_api_calls=true + OPENAI_API_KEY (else fail closed).
  - Only the FIXED goal is ever sent to a real provider (no arbitrary prompt).
  - The key is read ONLY from os.environ at call time (inside the provider); never
    from a file/.env/config/password file; never printed/committed.
  - The plan MUST pass PlanValidator; an invalid plan or a non-low-risk /
    non-allowlisted plan yields a BLOCKED package (no auto-fix, no execution).

Exit codes:
  0  review package built and REVIEW-READY (valid + low-risk + allowlisted)
  1  review package built but BLOCKED (invalid / not low-risk / not allowlisted)
  2  fail-closed (real-call requested without key / generation error)

Usage:
    .venv/bin/python scripts/openai_plan_review.py --dry-run            # offline fake plan
    .venv/bin/python scripts/openai_plan_review.py --plan-json <path>   # review an existing plan
    .venv/bin/python scripts/openai_plan_review.py --real-call          # one OpenAI plan, then review
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
from src.planner.fake_planner import MARKER_INSPECT, FakePlanner  # noqa: E402
from src.planner.plan_renderer import render_json, render_markdown  # noqa: E402
from src.planner.plan_validator import validate_plan  # noqa: E402
from src.planner.provider_planner import (  # noqa: E402
    LivePlanError, build_planner_from_config, parse_plan_from_text,
)
from src.planner.types import PlannerRequest  # noqa: E402

# Read-only skills allowed in a review-ready package (v0). Anything else -> BLOCKED.
# Kept in sync with src/planner/read_only_execution_gate.py (Story 2).
READONLY_SKILL_ALLOWLIST = ("inspect_project",)

FIXED_GOAL = "Create a safe read-only project status inspection plan. Do not execute anything."
API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_OUTPUT = ROOT / "runs" / "openai_plan_review"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _real_config() -> dict:
    return {"llm": {"provider": "openai", "model": "", "api_key_env": API_KEY_ENV,
                    "allow_real_api_calls": True, "redact_secrets": True, "fail_closed": True}}


def _plan_from_json_file(path: Path):
    """Rebuild a Plan from a plan.json (render_json format {"plan": {...}}) or a raw
    plan dict. Reuses the live parser, so non-JSON / bad shape raises LivePlanError."""
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    plan_dict = data.get("plan", data) if isinstance(data, dict) else {}
    # parse_plan_from_text expects the model-style JSON with a top-level "steps".
    return parse_plan_from_text(json.dumps(plan_dict), plan_dict.get("goal", FIXED_GOAL))


def assess_risk(plan) -> dict:
    """Per-step + overall risk. Blocked when any step is not low-risk or uses a
    non-allowlisted (read-only) skill."""
    per_step = []
    blocked_reasons: list[str] = []
    for s in plan.steps:
        not_low = s.risk_level != "low"
        not_allow = s.skill not in READONLY_SKILL_ALLOWLIST
        if not_low:
            blocked_reasons.append(f"step {s.id!r}: risk_level={s.risk_level!r} (not low)")
        if not_allow:
            blocked_reasons.append(f"step {s.id!r}: skill {s.skill!r} not in read-only allowlist")
        per_step.append({"id": s.id, "skill": s.skill, "risk_level": s.risk_level,
                         "allowlisted": not not_allow, "low_risk": not not_low})
    overall = "low" if all(p["low_risk"] for p in per_step) and per_step else (
        "n/a" if not per_step else "elevated")
    return {"per_step": per_step, "blocked_reasons": blocked_reasons, "overall_risk": overall}


def _write(out_dir: Path, name: str, text: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    path.write_text(redact_text(text), encoding="utf-8")  # redact every artifact
    return path


def _risk_md(plan, risk: dict, status: str) -> str:
    lines = ["# Risk Assessment", "",
             f"- overall_risk: {risk['overall_risk']}",
             f"- review_status: {status}",
             f"- read-only allowlist (v0): {', '.join(READONLY_SKILL_ALLOWLIST)}", "",
             "| step | skill | risk | low_risk | allowlisted |",
             "| --- | --- | --- | --- | --- |"]
    for p in risk["per_step"]:
        lines.append(f"| {redact_text(p['id'])} | {redact_text(p['skill'])} | {p['risk_level']} "
                     f"| {'yes' if p['low_risk'] else 'NO'} | {'yes' if p['allowlisted'] else 'NO'} |")
    lines.append("")
    if risk["blocked_reasons"]:
        lines.append("## BLOCKED reasons")
        for r in risk["blocked_reasons"]:
            lines.append(f"- {redact_text(r)}")
    else:
        lines.append("> All steps are low-risk and use only read-only allowlisted skills.")
    lines.append("")
    return "\n".join(lines)


def _approval_md(status: str) -> str:
    return (
        "# Approval Checklist\n\n"
        "**NOT APPROVED BY DEFAULT**\n\n"
        "**PLAN NOT EXECUTED**\n\n"
        "**HUMAN APPROVAL REQUIRED**\n\n"
        f"- review_status: {status}\n"
        "- APPROVED_FOR_READONLY_EXECUTION: false\n"
        "- reviewer: (none)\n\n"
        "## A human reviewer must confirm ALL before any read-only execution\n\n"
        "- [ ] I have read plan.json and plan_summary.md.\n"
        "- [ ] risk_assessment.md shows overall_risk = low and review_status = REVIEW-READY.\n"
        "- [ ] Every step uses only an allowlisted read-only skill (v0: inspect_project).\n"
        "- [ ] execution_preconditions.md are all satisfied.\n"
        "- [ ] No secret appears in any artifact.\n"
        "- [ ] I understand the plan is NEVER auto-executed and NEVER auto-repaired.\n\n"
        "To approve read-only execution, a human edits the line above to "
        "`APPROVED_FOR_READONLY_EXECUTION: true` and sets a non-empty `reviewer:`.\n"
        "Approval here authorizes ONLY allowlisted read-only execution — never patch, "
        "repair, apply, merge, staging, promotion, server, or browser actions.\n"
    )


def _preconditions_md(status: str) -> str:
    return (
        "# Execution Preconditions (read-only)\n\n"
        "A later read-only execution of this plan is permitted ONLY when ALL hold:\n\n"
        "1. The plan passes PlanValidator (`plan_valid: true`).\n"
        "2. review_status is REVIEW-READY (overall_risk = low; no blocked reasons).\n"
        "3. Every step's skill is in the read-only allowlist (v0: `inspect_project`).\n"
        "4. approval_checklist.md has `APPROVED_FOR_READONLY_EXECUTION: true` and a "
        "non-empty `reviewer:`.\n"
        "5. Execution is dry-run by default; a real run needs an explicit `--approved` "
        "flag plus a non-empty `--reviewer`.\n"
        "6. Execution context (e.g. the project_dir) comes from a vetted operator "
        "input — NEVER from the model's plan inputs, browser content, or run traces.\n"
        "7. No patch / repair / apply / merge / staging / promotion / server / browser "
        "/ raw-shell step is present or executed.\n\n"
        f"> Current review_status: {status}. Approval is NOT granted in this package.\n"
    )


def build_review_package(plan, out_dir: Path, *, mode: str, real_api_called: bool) -> dict:
    validation = validate_plan(plan)
    risk = assess_risk(plan)
    blocked = (not validation.valid) or bool(risk["blocked_reasons"])
    status = "BLOCKED" if blocked else "REVIEW-READY"

    plan_json = render_json(plan, validation)
    _write(out_dir, "plan.json", plan_json)
    _write(out_dir, "plan_summary.md", render_markdown(plan, validation))
    _write(out_dir, "risk_assessment.md", _risk_md(plan, risk, status))
    _write(out_dir, "approval_checklist.md", _approval_md(status))
    _write(out_dir, "execution_preconditions.md", _preconditions_md(status))

    report = {
        "generated_at": _now_iso(),
        "mode": mode,
        "real_api_called": real_api_called,
        "plan_executed": False,
        "auto_repair": False,
        "review_status": status,
        "plan_valid": validation.valid,
        "validation_errors": [redact_text(e) for e in validation.errors],
        "overall_risk": risk["overall_risk"],
        "blocked_reasons": [redact_text(r) for r in risk["blocked_reasons"]],
        "steps": len(plan.steps),
        "skills": plan.skills,
        "read_only_allowlist": list(READONLY_SKILL_ALLOWLIST),
        "approved_for_readonly_execution": False,
        "no_secret_in_plan": redact_text(plan_json) == plan_json,
    }
    safe = json.loads(redact_text(json.dumps(report, ensure_ascii=False)))
    _write(out_dir, "review_report.json", json.dumps(safe, ensure_ascii=False, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a human-review package from a plan (never executes it).")
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--dry-run", action="store_true",
                     help="use a deterministic offline fake inspect plan (default; no API)")
    src.add_argument("--real-call", action="store_true",
                     help="operator opt-in: generate ONE real OpenAI plan, then review it")
    src.add_argument("--plan-json", default="", help="review an existing plan.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="directory for the redacted review package (gitignored runs/ by default)")
    args = parser.parse_args(argv)

    out_dir = Path(args.output)
    mode = "real-call" if args.real_call else ("plan-json" if args.plan_json else "dry-run")
    real_api_called = False

    try:
        if args.real_call:
            if not os.environ.get(API_KEY_ENV):
                print(f"[BLOCKED] env var {API_KEY_ENV} is not set; cannot make a real call.",
                      file=sys.stderr)
                return 2
            planner = build_planner_from_config(_real_config(), root=ROOT, allow_real_call=True)
            resp = planner.live_plan(PlannerRequest(goal=FIXED_GOAL))
            real_api_called = True
            plan = resp.plan
        elif args.plan_json:
            plan = _plan_from_json_file(Path(args.plan_json))
        else:
            plan = FakePlanner().plan(PlannerRequest(marker=MARKER_INSPECT)).plan
    except (LivePlanError, LLMProviderError) as exc:
        # A blocked generation/parse still yields a (blocked) report — never auto-fix.
        out_dir.mkdir(parents=True, exist_ok=True)
        rpt = {"generated_at": _now_iso(), "mode": mode, "real_api_called": real_api_called,
               "plan_executed": False, "auto_repair": False, "review_status": "BLOCKED",
               "reason": redact_text(str(exc))[:400]}
        _write(out_dir, "review_report.json",
               json.dumps(json.loads(redact_text(json.dumps(rpt))), ensure_ascii=False, indent=2) + "\n")
        print(f"[BLOCKED] {redact_text(str(exc))[:300]}", file=sys.stderr)
        return 1

    report = build_review_package(plan, out_dir, mode=mode, real_api_called=real_api_called)
    print(redact_text(json.dumps(report, ensure_ascii=False, indent=2)))
    print(f"[REPORT] {out_dir}/review_report.json", file=sys.stderr)
    if report["review_status"] == "REVIEW-READY":
        print("[REVIEW-READY] package built; NOT APPROVED, PLAN NOT EXECUTED, human approval required.",
              file=sys.stderr)
        return 0
    print("[BLOCKED] review package built but the plan is not review-ready (no auto-fix).",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
