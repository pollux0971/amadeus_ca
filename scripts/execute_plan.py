"""execute_plan.py — run a *validated* fake plan through the execution bridge.

Controlled, allowlisted execution only. This is NOT a general autonomous agent:
it executes a deterministic fake-planner plan (or a plan.json it produced),
validates it, bridges it to an allowlisted skill sequence, and runs it under the
Safety Gate. Default is `--dry-run` (show the steps, execute nothing).

    # safe anywhere: print the executable sequence, run nothing
    python scripts/execute_plan.py --goal "FAKE_PLAN_FULL_BROWSER_E2E" \
        --marker FAKE_PLAN_FULL_BROWSER_E2E --dry-run

    # actually run a patch-only plan in the controlled fixture
    python scripts/execute_plan.py --marker FAKE_PLAN_PATCH_ONLY --execute

Rules:
- An unvalidated plan, an un-allowlisted skill, or an unapproved high-risk step
  fails closed (non-zero exit; nothing executes).
- No real API call, no env-var read, no direct shell, no autonomous replan.
- All written artifacts are redacted (no secret ever reaches disk).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm.redaction import redact_text
from src.planner.fake_planner import FakePlanner
from src.planner.plan_renderer import render_markdown
from src.planner.plan_validator import validate_plan
from src.planner.types import Plan, PlanStep, PlannerRequest
from src.planner.execution_bridge import (
    build_execution_sequence,
    execution_context_for,
    executable_markers,
)

# Default bridge success criteria per marker (used for a standalone --execute so
# score.json is meaningful; the evals carry their own explicit criteria).
_DEFAULT_CRITERIA = {
    "FAKE_PLAN_FULL_BROWSER_E2E": [
        "plan_created", "plan_valid", "allowed_skills_only",
        "start_local_server_invoked", "open_localhost_browser_invoked",
        "read_browser_console_invoked", "patch_file_and_run_tests_invoked",
        "post_patch_reverify_invoked", "score_1_0", "no_lingering_process",
        "no_secret_in_artifacts",
    ],
    "FAKE_PLAN_PATCH_ONLY": [
        "plan_created", "plan_valid", "execution_dry_run_safe", "allowed_skills_only",
        "patch_skill_invoked", "tests_pass", "no_secret_in_artifacts",
    ],
}


def _plan_from_file(path: Path) -> Plan:
    doc = json.loads(path.read_text(encoding="utf-8"))
    pd = doc.get("plan", doc)
    steps = [PlanStep(**s) for s in pd.get("steps", [])]
    return Plan(goal=pd.get("goal", ""), marker=pd.get("marker", ""),
                steps=steps, metadata=pd.get("metadata", {}))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute a validated fake plan via the bridge.")
    parser.add_argument("--plan", help="Path to a plan.json produced by plan_task.py.")
    parser.add_argument("--goal", default="", help="Goal text (when not using --plan).")
    parser.add_argument("--marker", default="", help="Plan marker (when not using --plan).")
    parser.add_argument("--approve-high-risk", action="store_true",
                        help="Allow high-risk steps that declare requires_approval.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Print steps; execute nothing (default).")
    mode.add_argument("--execute", action="store_true", help="Actually run the allowlisted sequence.")
    parser.add_argument("--runs-dir", default=str(ROOT / "runs"))
    args = parser.parse_args(argv)

    # Redact the goal at the door — it is a free-form prompt that could carry a
    # secret; marker detection uses known tokens, so redaction is safe here.
    safe_goal = redact_text(args.goal)

    # Build the plan: from a file, or deterministically from the marker/goal.
    if args.plan:
        plan = _plan_from_file(Path(args.plan))
        marker = plan.marker
    else:
        marker = args.marker
        plan = FakePlanner().plan(PlannerRequest(goal=safe_goal, marker=marker)).plan
        marker = plan.marker

    validation = validate_plan(plan)
    bridge = build_execution_sequence(plan, validation, approve_high_risk=args.approve_high_risk)

    execute = bool(args.execute)  # default (and --dry-run) => do not execute

    print(render_markdown(plan, validation), end="")
    print("## Execution bridge")
    print(f"- bridge_ok: {bridge.ok}")
    print(f"- approve_high_risk: {bridge.approved_high_risk}")
    if bridge.risk_notes:
        print(f"- risk_notes: {bridge.risk_notes}")
    if bridge.errors:
        print(f"- errors (fail-closed): {bridge.errors}")
    print("- executable sequence:")
    for s in bridge.steps:
        print(f"    - {s.plan_step_id} -> {s.skill} (as {s.alias}, risk={s.risk_level})")

    if not validation.valid or not bridge.ok:
        print("[BLOCKED] plan is not safely executable (validation/bridge failed closed).",
              file=sys.stderr)
        return 2

    if not execute:
        print("[DRY-RUN] no skill executed, nothing written.", file=sys.stderr)
        return 0

    # --execute: only known markers have a vetted execution context.
    if marker not in executable_markers() or not execution_context_for(marker):
        print(f"[BLOCKED] no execution context for marker {marker!r}; "
              f"executable markers: {executable_markers()}", file=sys.stderr)
        return 2

    from src.orchestrator.orchestrator import Orchestrator
    task = {
        "id": f"execute_plan_{marker.lower()}",
        "category": "planner_execution",
        "user_goal": plan.goal or marker,
        "goal": plan.goal,
        "marker": marker,
        "approve_high_risk": args.approve_high_risk,
        "success_criteria": _DEFAULT_CRITERIA.get(marker, ["plan_created", "plan_valid",
                                                           "allowed_skills_only"]),
    }
    orch = Orchestrator(task_id=task["id"], user_goal=task["user_goal"], runs_dir=args.runs_dir)
    run_dir = orch.run_eval_task(task)
    score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))
    status = "PASS" if score.get("task_success") else "FAIL"
    print(f"[{status}] execute {marker}  score={score.get('score')}  run={run_dir}", file=sys.stderr)
    return 0 if score.get("task_success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
