"""OpenAI Multi-Step Plan Review v0 — review a TWO-step read-only plan, NEVER run it.

Has the OpenAI live planner produce a fixed-goal, **two-step** read-only plan
(`inspect_project` then `list_project_files`) and emits a human-review package. It is
**plan-review only**: it NEVER executes a step, NEVER auto-repairs, and NEVER starts
repair / apply / merge / staging / promotion. It never adds the plan to an approved
fixture.

Safety:
  - **Dry-run by default** — uses a deterministic offline two-step plan; **no API call**.
  - **A real call needs `--real-call`** (one OpenAI call) + provider=openai +
    allow_real_api_calls=true + the OpenAI key present in `os.environ` (else fail closed).
  - The FIXED goal is the ONLY prompt (no arbitrary prompt); the key is read only from
    `os.environ` at call time (never `.env`, `password_and_api.txt`, or config; config
    stores the env-var NAME only); the key is never printed/committed.
  - The model must return a JSON plan that passes `PlanValidator`, contains ONLY
    `inspect_project` + `list_project_files`, is multi-step, and is all low-risk —
    otherwise a BLOCKED package is produced (no auto-fix).
  - The review package (`plan.json`, `plan_summary.md`, `risk_assessment.md`,
    `approval_checklist.md` [NOT APPROVED by default], `execution_preconditions.md`,
    `review_report.json`) is all redacted; `plan_executed` is always false.

Exit codes:
  0  review package built and REVIEW-READY (valid + multi-step + allowlisted + low-risk)
  1  review package built but BLOCKED (invalid / not multi-step / non-allowlisted / not low-risk)
  2  fail-closed (real-call requested without the key / generation error)

Usage:
    .venv/bin/python scripts/openai_multistep_plan_review.py --dry-run     # offline; no API
    .venv/bin/python scripts/openai_multistep_plan_review.py --real-call   # one OpenAI call
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import LLMProviderError, redact_text  # noqa: E402
from src.planner.plan_validator import validate_plan  # noqa: E402
from src.planner.provider_planner import (  # noqa: E402
    LIVE_PLAN_SYSTEM_PROMPT_MULTISTEP, LivePlanError, build_planner_from_config,
)
from src.planner.types import Plan, PlannerRequest, PlanStep  # noqa: E402

# Reuse the single-step review-package builder (one source of truth for artifacts).
_opr_spec = importlib.util.spec_from_file_location(
    "openai_plan_review", ROOT / "scripts" / "openai_plan_review.py")
opr = importlib.util.module_from_spec(_opr_spec)
_opr_spec.loader.exec_module(opr)

API_KEY_ENV = "OPENAI_API_KEY"
MULTISTEP_ALLOWED = ("inspect_project", "list_project_files")
# The FIXED goal — no arbitrary prompt is permitted.
MULTISTEP_GOAL = (
    "Create a safe read-only two-step project inspection plan:\n"
    "1. inspect_project\n"
    "2. list_project_files\n"
    "Do not execute anything."
)
DEFAULT_OUTPUT = ROOT / "runs" / "openai_multistep_plan_review"


def _real_config() -> dict:
    return {"llm": {"provider": "openai", "model": "", "api_key_env": API_KEY_ENV,
                    "allow_real_api_calls": True, "redact_secrets": True, "fail_closed": True}}


def _deterministic_two_step_plan() -> Plan:
    """Offline, deterministic two-step plan used for --dry-run (no API call)."""
    return Plan(
        goal=MULTISTEP_GOAL,
        marker="",
        steps=[
            PlanStep(id="inspect", skill="inspect_project",
                     inputs={"project_dir": "${project_dir}"},
                     expected_outputs=["project_type"], success_criteria=["project_inspected"],
                     risk_level="low", requires_approval=False, depends_on=[]),
            PlanStep(id="list_files", skill="list_project_files",
                     inputs={"project_dir": "${project_dir}", "max_files": 200},
                     expected_outputs=["file_count", "files"], success_criteria=["files_listed"],
                     risk_level="low", requires_approval=False, depends_on=["inspect"]),
        ],
        metadata={"planner": "provider_backed_live", "source": "dry-run-deterministic",
                  "kind": "multistep_review"},
    )


def _multistep_markers(plan: Plan) -> dict:
    skills = plan.skills
    return {
        "multistep_plan_detected": len(plan.steps) >= 2,
        "inspect_project_present": "inspect_project" in skills,
        "list_project_files_present": "list_project_files" in skills,
        "allowlisted_skills_only": bool(skills) and all(s in MULTISTEP_ALLOWED for s in skills),
        "low_risk_only": bool(plan.steps) and all(s.risk_level == "low" for s in plan.steps),
    }


def _emit(out_dir: Path, report: dict) -> None:
    safe = json.loads(redact_text(json.dumps(report, ensure_ascii=False)))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "review_report.json").write_text(
        json.dumps(safe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(redact_text(json.dumps(report, ensure_ascii=False, indent=2)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a human-review package for a two-step read-only OpenAI plan (never runs it).")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true",
                   help="use a deterministic offline two-step plan (default; no API)")
    g.add_argument("--real-call", action="store_true",
                   help="operator opt-in: generate ONE real OpenAI two-step plan, then review it")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="directory for the redacted review package (gitignored runs/ by default)")
    args = parser.parse_args(argv)

    out_dir = Path(args.output)
    mode = "real-call" if args.real_call else "dry-run"
    real_api_called = False

    try:
        if args.real_call:
            if not os.environ.get(API_KEY_ENV):
                print(f"[BLOCKED] env var {API_KEY_ENV} is not set; cannot make a real call.",
                      file=sys.stderr)
                return 2
            planner = build_planner_from_config(_real_config(), root=ROOT, allow_real_call=True)
            resp = planner.live_plan(PlannerRequest(goal=MULTISTEP_GOAL),
                                     system_prompt=LIVE_PLAN_SYSTEM_PROMPT_MULTISTEP)
            real_api_called = True
            plan = resp.plan
        else:
            plan = _deterministic_two_step_plan()
    except (LivePlanError, LLMProviderError) as exc:
        out_dir.mkdir(parents=True, exist_ok=True)
        report = {"mode": mode, "real_api_called": real_api_called, "plan_executed": False,
                  "auto_repair": False, "review_status": "BLOCKED",
                  "reason": redact_text(str(exc))[:400]}
        _emit(out_dir, report)
        print(f"[BLOCKED] {redact_text(str(exc))[:300]}", file=sys.stderr)
        return 1

    # Build the review package (validates + assesses risk + writes redacted artifacts;
    # approval defaults to NOT APPROVED; never executes).
    report = opr.build_review_package(plan, out_dir, mode=mode, real_api_called=real_api_called)

    # Augment with multi-step markers and re-write the (redacted) review_report.json.
    markers = _multistep_markers(plan)
    report.update(markers)
    report["openai_plan_created"] = bool(plan.steps)
    report["plan_not_executed"] = True
    multistep_ok = all(markers.values())
    base_ready = report.get("review_status") == "REVIEW-READY"
    report["review_status"] = "REVIEW-READY" if (base_ready and multistep_ok) else "BLOCKED"
    _emit(out_dir, report)

    print(f"[REPORT] {out_dir}/review_report.json", file=sys.stderr)
    if report["review_status"] == "REVIEW-READY":
        print("[REVIEW-READY] two-step plan reviewed; NOT APPROVED, PLAN NOT EXECUTED, "
              "human approval required.", file=sys.stderr)
        return 0
    print("[BLOCKED] multi-step review package built but the plan is not review-ready "
          "(no auto-fix).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
