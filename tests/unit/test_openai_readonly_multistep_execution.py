import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RUNNER = ROOT / "scripts" / "run_openai_readonly_execution_gate.py"
RUN_EVAL = ROOT / "scripts" / "run_eval.py"
EVAL = ROOT / "evals" / "planner" / "openai_readonly_multistep_execution_gate.yaml"
FIXTURE = ROOT / "fixtures" / "openai_planner" / "approved_readonly_plan_multistep"
SINGLE_EVALS = [
    ROOT / "evals" / "planner" / "openai_readonly_execution_gate.yaml",
    ROOT / "evals" / "planner" / "openai_readonly_list_files_execution_gate.yaml",
]
FAKE_KEY = "sk-" + "d" * 44

from src.planner.read_only_execution_gate import (  # noqa: E402
    READONLY_ALLOWLIST, ApprovalRecord, ReadOnlyExecutionError, execute_readonly_plan,
    validate_readonly_plan,
)
from src.planner.types import Plan, PlanStep  # noqa: E402

REQUIRED_CRITERIA = [
    "approved_plan_loaded", "approval_marker_checked", "reviewer_present", "plan_valid",
    "allowlisted_skills_only", "inspect_project_invoked", "list_project_files_invoked",
    "execution_order_correct", "each_step_executed_once", "no_file_content_read",
    "excluded_paths_not_listed", "no_browser_patch_console_repair_promotion",
    "no_raw_shell", "no_secret_in_artifacts", "stable_safety_promotion_untouched",
    "score_1_0",
]


def _two_step_plan():
    return Plan(goal="g", steps=[
        PlanStep(id="inspect", skill="inspect_project", risk_level="low"),
        PlanStep(id="list_files", skill="list_project_files", risk_level="low",
                 depends_on=["inspect"]),
    ])


def _approved():
    return ApprovalRecord(approved_marker=True, reviewer="alice")


def _run_gate(args, env=None):
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(RUNNER), *args, "--output", tmp],
                           capture_output=True, text=True, cwd=str(ROOT), env=env)
        rep = {}
        p = Path(tmp) / "gate_report.json"
        if p.exists():
            rep["text"] = p.read_text(encoding="utf-8")
            rep["json"] = json.loads(rep["text"])
    return r, rep


def _eval(task):
    with tempfile.TemporaryDirectory() as tmp:
        return subprocess.run([sys.executable, str(RUN_EVAL), "--task", str(task),
                               "--runs-dir", tmp], capture_output=True, text=True, cwd=str(ROOT))


def test_fixture_and_eval_exist():
    assert EVAL.exists()
    assert FIXTURE.exists() and (FIXTURE / "plan.json").exists()
    assert (FIXTURE / "approval_checklist.md").exists()


def test_allowlist_not_expanded():
    assert READONLY_ALLOWLIST == ("inspect_project", "list_project_files")


def test_executes_both_steps_in_order():
    out = execute_readonly_plan(_two_step_plan(), _approved(), approved=True,
                                project_dir=str(ROOT))
    assert out["executed"] is True
    assert out["steps_executed"] == 2
    assert out["executed_skills_in_order"] == ["inspect_project", "list_project_files"]
    order = out["execution_order"]
    assert [e["order"] for e in order] == [0, 1]
    assert [e["skill"] for e in order] == ["inspect_project", "list_project_files"]
    # each step id exactly once
    ids = [e["id"] for e in order]
    assert ids == ["inspect", "list_files"] and len(set(ids)) == 2
    assert out["retried"] is False and out["auto_repair"] is False and out["replanned"] is False


def test_fail_closed_on_a_failing_step_no_retry():
    # inspect_project on a missing dir fails -> the gate must raise and stop (no retry).
    try:
        execute_readonly_plan(_two_step_plan(), _approved(), approved=True,
                              project_dir="/nonexistent/path/xyz")
        assert False, "expected ReadOnlyExecutionError"
    except ReadOnlyExecutionError as exc:
        assert "step_failed" in str(exc)


def test_forbidden_skill_in_multistep_is_refused():
    bad = Plan(goal="g", steps=[
        PlanStep(id="a", skill="inspect_project", risk_level="low"),
        PlanStep(id="b", skill="patch_file_and_run_tests", risk_level="low", depends_on=["a"]),
    ])
    assert validate_readonly_plan(bad).ok is False
    try:
        execute_readonly_plan(bad, _approved(), approved=True, project_dir=str(ROOT))
        assert False, "expected ReadOnlyExecutionError"
    except ReadOnlyExecutionError:
        pass


def test_runner_default_is_inspect_project():
    r, _ = _run_gate(["--dry-run"])
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["skills"] == ["inspect_project"]


def test_runner_execute_multistep():
    r, _ = _run_gate(["--execute", "--fixture", "multistep"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["status"] == "EXECUTED"
    assert data["skills"] == ["inspect_project", "list_project_files"]
    assert data["real_api_called"] is False
    assert data["execution"]["executed_skills_in_order"] == [
        "inspect_project", "list_project_files"]


def test_multistep_eval_scores_1_0():
    r = _eval(EVAL)
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "score=1.0" in r.stdout
    for c in REQUIRED_CRITERIA:
        assert f"[x] {c}" in r.stdout, c


def test_single_step_evals_still_1_0():
    for ev in SINGLE_EVALS:
        r = _eval(ev)
        assert r.returncode == 0, (ev, r.stdout, r.stderr)
        assert "score=1.0" in r.stdout


def test_no_secret_in_output_with_key_in_env():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    r, rep = _run_gate(["--execute", "--fixture", "multistep"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
    if "text" in rep:
        assert FAKE_KEY not in rep["text"]


def test_no_file_content_in_multistep_results():
    out = execute_readonly_plan(_two_step_plan(), _approved(), approved=True,
                                project_dir=str(ROOT))
    for r in out["results"]:
        res = r["result"]
        for k in ("content", "file_content", "contents", "text"):
            assert k not in res
        if r["skill"] == "list_project_files":
            assert res["content_read"] is False


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
