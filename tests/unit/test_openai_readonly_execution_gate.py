import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "execute_openai_readonly_plan.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
GATE_SRC = (ROOT / "src" / "planner" / "read_only_execution_gate.py").read_text(encoding="utf-8")
EVAL = ROOT / "evals" / "planner" / "openai_readonly_plan_execution.yaml"
FIXTURE = ROOT / "fixtures" / "openai_planner" / "approved_readonly_plan"
FAKE_KEY = "sk-" + "d" * 44

from src.planner.read_only_execution_gate import (  # noqa: E402
    APPROVAL_MARKER, FORBIDDEN_SKILLS, READONLY_ALLOWLIST, ApprovalRecord,
    ReadOnlyExecutionError, authorize, execute_readonly_plan, parse_approval,
    validate_readonly_plan,
)
from src.planner.types import Plan, PlanStep  # noqa: E402


def _inspect_plan(risk="low", skill="inspect_project"):
    return Plan(goal="g", steps=[PlanStep(id="inspect", skill=skill, risk_level=risk)])


def _approved(reviewer="alice"):
    return ApprovalRecord(approved_marker=True, reviewer=reviewer)


def _run(args, env=None):
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(SCRIPT), *args, "--output", tmp],
                           capture_output=True, text=True, cwd=str(ROOT), env=env)
        rep = {}
        p = Path(tmp) / "execution_report.json"
        if p.exists():
            rep["text"] = p.read_text(encoding="utf-8")
            rep["json"] = json.loads(rep["text"])
    return r, rep


# -------- gate unit behavior --------
def test_allowlist_is_readonly_only():
    # v0 expanded to add the content-free list_project_files; nothing else.
    assert READONLY_ALLOWLIST == ("inspect_project", "list_project_files")


def test_validate_readonly_plan_accepts_clean_inspect_plan():
    assert validate_readonly_plan(_inspect_plan()).ok is True


def test_non_allowlisted_and_forbidden_skills_refused():
    for skill in ("patch_file_and_run_tests", "start_local_server",
                  "open_localhost_browser", "read_browser_console", "raw_shell",
                  "repair", "apply", "merge", "staging_promote", "exec", "eval", "bash"):
        assert skill in FORBIDDEN_SKILLS or skill not in READONLY_ALLOWLIST
        res = validate_readonly_plan(_inspect_plan(skill=skill))
        assert res.ok is False, skill


def test_non_low_risk_refused():
    assert validate_readonly_plan(_inspect_plan(risk="medium")).ok is False
    assert validate_readonly_plan(_inspect_plan(risk="high")).ok is False


def test_authorize_requires_all_conditions():
    plan = _inspect_plan()
    # missing --approved
    assert authorize(plan, _approved(), approved=False).ok is False
    # missing marker
    assert authorize(plan, ApprovalRecord(approved_marker=False, reviewer="a"),
                     approved=True).ok is False
    # empty reviewer
    assert authorize(plan, ApprovalRecord(approved_marker=True, reviewer=""),
                     approved=True).ok is False
    assert authorize(plan, ApprovalRecord(approved_marker=True, reviewer="(none)"),
                     approved=True).ok is False
    # all present
    assert authorize(plan, _approved(), approved=True).ok is True


def test_parse_approval_reads_marker_and_reviewer():
    txt = "stuff\n- APPROVED_FOR_READONLY_EXECUTION: true\n- reviewer: bob\n"
    a = parse_approval(txt)
    assert a.approved_marker is True and a.reviewer == "bob" and a.reviewer_ok


def test_execute_refuses_unauthorized():
    try:
        execute_readonly_plan(_inspect_plan(), _approved(), approved=False, project_dir=str(ROOT))
        assert False, "expected ReadOnlyExecutionError"
    except ReadOnlyExecutionError:
        pass


def test_execute_refuses_forbidden_skill_even_if_approved():
    bad = _inspect_plan(skill="patch_file_and_run_tests")
    try:
        execute_readonly_plan(bad, _approved(), approved=True, project_dir=str(ROOT))
        assert False, "expected ReadOnlyExecutionError"
    except ReadOnlyExecutionError:
        pass


def test_execute_runs_inspect_project_readonly():
    out = execute_readonly_plan(_inspect_plan(), _approved(), approved=True,
                                project_dir=str(ROOT))
    assert out["executed"] is True and out["read_only"] is True
    assert out["auto_repair"] is False and out["replanned"] is False
    assert out["steps_executed"] == 1
    assert out["results"][0]["skill"] == "inspect_project"
    assert out["results"][0]["status"] == "ok"


# -------- script behavior --------
def test_script_and_eval_exist():
    assert SCRIPT.exists() and EVAL.exists()
    assert FIXTURE.exists() and (FIXTURE / "plan.json").exists()
    assert (FIXTURE / "approval_checklist.md").exists()


def test_dry_run_executes_nothing():
    r, rep = _run(["--dry-run"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["mode"] == "dry-run"
    assert data["plan_executed"] is False
    assert data["authorized"] is False  # no --approved
    assert data["plan_readonly_executable"] is True


def test_default_without_approved_does_not_execute():
    r, _ = _run([])  # no --approved, no --dry-run
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["plan_executed"] is False


def test_approved_run_executes_readonly():
    r, rep = _run(["--approved", "--reviewer", "alice", "--project-dir", str(ROOT)])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["status"] == "EXECUTED"
    assert data["plan_executed"] is True
    assert data["real_api_called"] is False
    assert data["execution"]["read_only"] is True


def test_no_secret_in_output_even_with_key_in_env():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    r, rep = _run(["--approved", "--reviewer", "alice"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
    if "text" in rep:
        assert FAKE_KEY not in rep["text"]


def test_script_makes_no_openai_call():
    # The execution script must never construct/call a provider or read the key.
    assert "real-call" not in SCRIPT_SRC.lower()
    assert "build_provider" not in SCRIPT_SRC and "build_planner_from_config" not in SCRIPT_SRC
    assert "os.environ" not in SCRIPT_SRC
    assert "--approved" in SCRIPT_SRC and "--dry-run" in SCRIPT_SRC


def test_gate_does_not_use_shell_or_repair():
    # (skill NAMES like "subprocess"/"staging_promote" appear only in the denylist;
    # the gate must not actually import/use a shell, repair, or executor runtime.)
    for forbidden in ("import subprocess", "subprocess.run", "os.system", "shell=True",
                      "from src.repair", "import staging_promote",
                      "build_execution_sequence", "popen", "Popen"):
        assert forbidden not in GATE_SRC, forbidden
    assert "redact" in GATE_SRC
    # the denylist must explicitly name the non-read-only / shell skills
    assert "patch_file_and_run_tests" in GATE_SRC and "raw_shell" in GATE_SRC


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
