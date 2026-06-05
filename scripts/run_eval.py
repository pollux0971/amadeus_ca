from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.skills_runtime.simple_yaml import load_yaml
from src.orchestrator.orchestrator import Orchestrator


def resolve_task_path(task: str) -> Path | None:
    """Accept a path, or a bare task id to be searched under evals/."""
    candidate = Path(task)
    if candidate.exists():
        return candidate
    candidate = ROOT / task
    if candidate.exists():
        return candidate
    matches = sorted((ROOT / "evals").rglob(f"{task}.yaml"))
    return matches[0] if matches else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an eval task through the harness.")
    parser.add_argument("--task", required=True, help="Path to an eval yaml, or a bare task id under evals/")
    parser.add_argument("--runs-dir", default=str(ROOT / "runs"))
    args = parser.parse_args()

    task_path = resolve_task_path(args.task)
    if task_path is None:
        print(f"[FAIL] could not find eval task: {args.task}")
        return 2

    task = load_yaml(task_path)
    if not task.get("id") or not task.get("user_goal"):
        print(f"[FAIL] eval task missing required fields (id, user_goal): {task_path}")
        return 2

    orch = Orchestrator(task_id=task["id"], user_goal=task["user_goal"], runs_dir=args.runs_dir)
    run_dir = orch.run_eval_task(task, eval_path=task_path)

    score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))
    status = "PASS" if score.get("task_success") else "FAIL"
    print(f"[{status}] {task['id']}  score={score.get('score')}  run={run_dir}")
    for r in score.get("criteria_results", []):
        mark = "x" if r.get("passed") else " "
        print(f"  [{mark}] {r.get('criterion')}")
    if not score.get("task_success"):
        print(f"  failure: {score.get('failure', {}).get('root_cause')}")
        print(f"  report : {run_dir / 'failure_report.md'}")
    return 0 if score.get("task_success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
