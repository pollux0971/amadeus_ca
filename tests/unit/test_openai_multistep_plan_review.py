import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "openai_multistep_plan_review.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
RUN_EVAL = ROOT / "scripts" / "run_eval.py"
EVAL = ROOT / "evals" / "planner" / "openai_multistep_plan_review.yaml"
MS_EXEC_EVAL = ROOT / "evals" / "planner" / "openai_readonly_multistep_execution_gate.yaml"
FAKE_KEY = "sk-" + "d" * 44

_spec = importlib.util.spec_from_file_location("openai_multistep_plan_review", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

PKG_FILES = ("plan.json", "plan_summary.md", "risk_assessment.md",
             "approval_checklist.md", "review_report.json")
REQUIRED_CRITERIA = [
    "dry_run_safe", "real_call_requires_operator_opt_in", "openai_plan_created",
    "plan_valid", "multistep_plan_detected", "inspect_project_present",
    "list_project_files_present", "allowlisted_skills_only", "low_risk_only",
    "review_package_created", "approval_not_granted", "plan_not_executed",
    "no_secret_in_artifacts", "no_auto_repair", "stable_safety_promotion_untouched",
    "score_1_0",
]


def _run(args, env=None):
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(SCRIPT), *args, "--output", tmp],
                           capture_output=True, text=True, cwd=str(ROOT), env=env)
        files = {}
        for name in PKG_FILES:
            p = Path(tmp) / name
            if p.exists():
                files[name] = p.read_text(encoding="utf-8")
    return r, files


def _env_without_key():
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    return env


def test_script_and_eval_exist():
    assert SCRIPT.exists() and EVAL.exists()


def test_fixed_goal_is_two_step_inspect_then_list():
    assert "inspect_project" in mod.MULTISTEP_GOAL
    assert "list_project_files" in mod.MULTISTEP_GOAL
    assert mod.MULTISTEP_ALLOWED == ("inspect_project", "list_project_files")


def test_dry_run_builds_review_ready_multistep_package_no_api():
    r, files = _run(["--dry-run"], env=_env_without_key())
    assert r.returncode == 0, r.stderr
    for name in PKG_FILES:
        assert name in files, name
    data = json.loads(r.stdout)
    assert data["review_status"] == "REVIEW-READY"
    assert data["real_api_called"] is False
    assert data["plan_not_executed"] is True
    assert data["auto_repair"] is False
    assert data["multistep_plan_detected"] is True
    assert data["inspect_project_present"] and data["list_project_files_present"]
    assert data["allowlisted_skills_only"] and data["low_risk_only"]
    assert data["skills"] == ["inspect_project", "list_project_files"]
    assert data["approved_for_readonly_execution"] is False


def test_default_is_dry_run_no_api():
    r, _ = _run([], env=_env_without_key())
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["real_api_called"] is False


def test_real_call_blocked_without_key():
    r, _ = _run(["--real-call"], env=_env_without_key())
    assert r.returncode == 2, r.stderr
    assert "blocked" in r.stderr.lower()


def test_approval_remains_not_approved():
    r, files = _run(["--dry-run"], env=_env_without_key())
    chk = files["approval_checklist.md"]
    assert "NOT APPROVED BY DEFAULT" in chk
    assert "PLAN NOT EXECUTED" in chk
    assert "APPROVED_FOR_READONLY_EXECUTION: false" in chk


def test_no_secret_in_output_even_with_key_in_env():
    env = _env_without_key()
    env["OPENAI_API_KEY"] = FAKE_KEY
    r, files = _run(["--dry-run"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
    for t in files.values():
        assert FAKE_KEY not in t


def test_script_safety_invariants_in_source():
    assert "--real-call" in SCRIPT_SRC and "--dry-run" in SCRIPT_SRC
    assert "os.environ.get(API_KEY_ENV)" in SCRIPT_SRC
    assert "redact" in SCRIPT_SRC
    # review-only: must not import an executor / repair / promotion runtime
    for forbidden in ("execute_readonly_plan", "build_execution_sequence",
                      "from src.repair", "staging_promote"):
        assert forbidden not in SCRIPT_SRC, forbidden


def test_does_not_write_into_approved_fixture():
    # The script must never target an approved fixture dir as its output.
    assert "fixtures/openai_planner" not in SCRIPT_SRC


def test_review_eval_scores_1_0():
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(RUN_EVAL), "--task", str(EVAL),
                            "--runs-dir", tmp], capture_output=True, text=True, cwd=str(ROOT))
        assert r.returncode == 0, (r.stdout, r.stderr)
        assert "score=1.0" in r.stdout
        for c in REQUIRED_CRITERIA:
            assert f"[x] {c}" in r.stdout, c


def test_multistep_execution_eval_still_1_0():
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(RUN_EVAL), "--task", str(MS_EXEC_EVAL),
                            "--runs-dir", tmp], capture_output=True, text=True, cwd=str(ROOT))
        assert r.returncode == 0, (r.stdout, r.stderr)
        assert "score=1.0" in r.stdout


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
