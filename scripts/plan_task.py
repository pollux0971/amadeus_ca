"""plan_task.py — turn a goal/marker into a validated, redacted plan.

Fake-only, plan-only. This script NEVER executes the plan: it builds a
declarative plan with `FakePlanner` (offline, deterministic), validates it, and
prints a redacted summary. With `--write` it persists the plan (default: no
write). No real API call, no env-var read, no skill execution.

Examples:
    python scripts/plan_task.py --goal "FAKE_PLAN_FULL_BROWSER_E2E" \
        --marker FAKE_PLAN_FULL_BROWSER_E2E --json
    python scripts/plan_task.py --goal "inspect it" \
        --marker FAKE_PLAN_INSPECT_PROJECT --write runs/plans/inspect.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.planner.fake_planner import FakePlanner
from src.planner.plan_renderer import render_json, render_markdown
from src.planner.plan_validator import validate_plan
from src.planner.types import PlannerRequest


def _default_write_path(marker: str, goal: str) -> Path:
    # Deterministic, non-secret filename — no timestamp, no goal echo.
    stem = (marker or "noop").lower().replace("fake_plan_", "").strip("_") or "plan"
    return ROOT / "runs" / "plans" / f"{stem}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build & validate a plan (fake-only, no execution).")
    parser.add_argument("--goal", default="", help="User goal text.")
    parser.add_argument("--marker", default="", help="Explicit plan marker (optional).")
    parser.add_argument("--config", default=str(ROOT / "config" / "config.json"),
                        help="Config path (informational; planner stays fake-only).")
    parser.add_argument("--json", action="store_true", help="Emit redacted JSON instead of markdown.")
    parser.add_argument("--write", nargs="?", const="__default__", default=None,
                        help="Write the redacted plan JSON to a path (default: do not write).")
    args = parser.parse_args(argv)

    # Fake-only: the planner constructs its own offline FakeLLMProvider. The
    # --config flag is accepted for interface symmetry but never selects a real
    # provider here; nothing in this script reads an env-var key value.
    planner = FakePlanner()
    response = planner.plan(PlannerRequest(goal=args.goal, marker=args.marker))
    plan = response.plan
    validation = validate_plan(plan)

    json_doc = render_json(plan, validation)
    if args.json:
        print(json_doc)
    else:
        print(render_markdown(plan, validation))

    if args.write is not None:
        out = (_default_write_path(plan.marker, plan.goal)
               if args.write == "__default__" else Path(args.write))
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        # render_json is already redacted — no secret can reach the file.
        out.write_text(json_doc, encoding="utf-8")
        print(f"[WROTE] {out}", file=sys.stderr)

    # Plan-only: exit non-zero if the produced plan is invalid, but never execute.
    return 0 if validation.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
