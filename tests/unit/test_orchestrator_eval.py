import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.skills_runtime.simple_yaml import load_yaml
from src.orchestrator.orchestrator import Orchestrator


def _run(eval_rel: str):
    task_path = ROOT / eval_rel
    task = load_yaml(task_path)
    tmp = tempfile.mkdtemp(prefix="harness_test_runs_")
    orch = Orchestrator(task_id=task["id"], user_goal=task["user_goal"], runs_dir=tmp)
    run_dir = orch.run_eval_task(task, eval_path=task_path)
    score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))
    return run_dir, score


def test_walking_skeleton_passes_and_emits_all_files():
    run_dir, score = _run("evals/walking_skeleton/inspect_only.yaml")
    assert score["task_success"] is True
    assert score["score"] == 1.0
    # Required run files exist.
    for name in ("trace.jsonl", "score.json", "summary.md", "task.yaml"):
        assert (run_dir / name).exists(), f"missing {name}"
    # One trace event per required skill.
    lines = (run_dir / "trace.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["actor"]["skill_id"] == "inspect_project"
    assert event["evaluation"]["step_success"] is True


def test_vite_slice_runs_all_steps_and_reports_placeholder_gap():
    run_dir, score = _run("evals/cli_browser_integration/vite_login_bug.yaml")
    # Five required skills -> five trace events.
    lines = (run_dir / "trace.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
    # Honest partial: server/browser/console pass, patch+tests fail.
    assert score["task_success"] is False
    crit = {r["criterion"]: r["passed"] for r in score["criteria_results"]}
    assert crit["dev_server_started"] is True
    assert crit["browser_opened_localhost"] is True
    assert crit["console_error_collected"] is True
    assert crit["source_file_patched"] is False
    assert crit["tests_pass"] is False
    # Failure is correctly attributed to the placeholder patch skill.
    assert "not_implemented" in score["failure"]["root_cause"]
    assert (run_dir / "failure_report.md").exists()


def test_forbidden_actions_not_triggered_on_clean_run():
    _, score = _run("evals/cli_browser_integration/vite_login_bug.yaml")
    assert all(not r["triggered"] for r in score["forbidden_action_results"])
    assert score["metrics"]["safety_incidents"] == 0


def test_metrics_count_cli_and_browser_steps():
    _, score = _run("evals/cli_browser_integration/vite_login_bug.yaml")
    m = score["metrics"]
    assert m["total_steps"] == 5
    # inspect_project(cli) + start_local_server(cli/bridge) + patch(cli) = 3 cli
    assert m["cli_command_count"] == 3
    # open_localhost_browser + read_browser_console = 2 browser
    assert m["browser_action_count"] == 2


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
