from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.skills_runtime.simple_yaml import load_yaml
from src.orchestrator.orchestrator import Orchestrator


# Demos backed by a real eval task run through the harness.
DEMO_EVALS = {
    "walking_skeleton": "evals/walking_skeleton/inspect_only.yaml",
    "vite_login_bug": "evals/cli_browser_integration/vite_login_bug.yaml",
}

# Placeholder demo (kept so the original no-op path is still reachable).
PLACEHOLDER_GOALS = {
    "hello": "Run a placeholder harness demo.",
}


def run_eval_demo(eval_rel: str) -> int:
    task_path = ROOT / eval_rel
    task = load_yaml(task_path)
    orch = Orchestrator(task_id=task["id"], user_goal=task["user_goal"])
    run_dir = orch.run_eval_task(task, eval_path=task_path)
    score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))
    status = "PASS" if score.get("task_success") else "FAIL"
    print(f"[{status}] demo `{task['id']}` score={score.get('score')} run={run_dir}")
    for r in score.get("criteria_results", []):
        mark = "x" if r.get("passed") else " "
        print(f"  [{mark}] {r.get('criterion')}")
    if not score.get("task_success"):
        print(f"  failure: {score.get('failure', {}).get('root_cause')}")
    return 0


def run_placeholder_demo(demo: str) -> int:
    orch = Orchestrator(task_id=demo, user_goal=PLACEHOLDER_GOALS[demo])
    run_dir = orch.run_placeholder()
    print(f"[PASS] demo placeholder completed: {run_dir}")
    return 0


def main() -> int:
    choices = sorted({*DEMO_EVALS, *PLACEHOLDER_GOALS})
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", default="walking_skeleton", choices=choices)
    args = parser.parse_args()

    if args.demo in DEMO_EVALS:
        return run_eval_demo(DEMO_EVALS[args.demo])
    return run_placeholder_demo(args.demo)


if __name__ == "__main__":
    raise SystemExit(main())
