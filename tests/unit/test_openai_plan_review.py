import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "openai_plan_review.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
EXAMPLE = ROOT / "reports" / "openai_plan_review_v0" / "example"
FAKE_KEY = "sk-" + "d" * 44

_spec = importlib.util.spec_from_file_location("openai_plan_review", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

from src.planner.types import Plan, PlanStep  # noqa: E402

PKG_FILES = ("plan.json", "plan_summary.md", "risk_assessment.md",
             "approval_checklist.md", "execution_preconditions.md", "review_report.json")


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


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_builds_review_ready_package():
    r, files = _run(["--dry-run"], env=_env_without_key())
    assert r.returncode == 0, r.stderr
    for name in PKG_FILES:
        assert name in files, f"missing {name}"
    data = json.loads(r.stdout)
    assert data["review_status"] == "REVIEW-READY"
    assert data["real_api_called"] is False
    assert data["plan_executed"] is False
    assert data["auto_repair"] is False
    assert data["plan_valid"] is True
    assert data["approved_for_readonly_execution"] is False
    assert data["no_secret_in_plan"] is True
    assert data["skills"] == ["inspect_project"]


def test_approval_checklist_required_phrases():
    r, files = _run(["--dry-run"], env=_env_without_key())
    chk = files["approval_checklist.md"]
    assert "NOT APPROVED BY DEFAULT" in chk
    assert "PLAN NOT EXECUTED" in chk
    assert "HUMAN APPROVAL REQUIRED" in chk
    assert "APPROVED_FOR_READONLY_EXECUTION: false" in chk


def test_assess_risk_blocks_non_low_or_non_allowlisted():
    # non-allowlisted skill
    p1 = Plan(goal="g", steps=[PlanStep(id="a", skill="patch_file_and_run_tests",
                                        risk_level="low")])
    r1 = mod.assess_risk(p1)
    assert r1["blocked_reasons"], "patch skill should be blocked"
    # non-low risk
    p2 = Plan(goal="g", steps=[PlanStep(id="a", skill="inspect_project",
                                        risk_level="medium")])
    r2 = mod.assess_risk(p2)
    assert r2["blocked_reasons"], "medium risk should be blocked"
    # clean
    p3 = Plan(goal="g", steps=[PlanStep(id="a", skill="inspect_project", risk_level="low")])
    assert not mod.assess_risk(p3)["blocked_reasons"]


def test_plan_json_with_forbidden_skill_is_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        plan_json = Path(tmp) / "p.json"
        plan_json.write_text(json.dumps({"plan": {"goal": "g", "steps": [
            {"id": "a", "skill": "raw_shell", "risk_level": "low"}]}}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "--plan-json", str(plan_json),
                            "--output", tmp], capture_output=True, text=True, cwd=str(ROOT))
        assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
        assert json.loads(r.stdout)["review_status"] == "BLOCKED"


def test_committed_example_is_review_ready_and_not_approved():
    assert EXAMPLE.exists()
    for name in PKG_FILES:
        assert (EXAMPLE / name).exists(), f"example missing {name}"
    report = json.loads((EXAMPLE / "review_report.json").read_text(encoding="utf-8"))
    assert report["review_status"] == "REVIEW-READY"
    assert report["approved_for_readonly_execution"] is False
    chk = (EXAMPLE / "approval_checklist.md").read_text(encoding="utf-8")
    assert "APPROVED_FOR_READONLY_EXECUTION: false" in chk


def test_no_secret_in_output_even_with_key_in_env():
    env = _env_without_key()
    env["OPENAI_API_KEY"] = FAKE_KEY
    r, files = _run(["--dry-run"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
    for text in files.values():
        assert FAKE_KEY not in text


def test_real_call_blocked_without_key():
    r, _ = _run(["--real-call"], env=_env_without_key())
    assert r.returncode == 2, r.stderr
    assert "blocked" in r.stderr.lower()


def test_script_safety_invariants_in_source():
    assert "--real-call" in SCRIPT_SRC and "--dry-run" in SCRIPT_SRC
    assert "os.environ.get(API_KEY_ENV)" in SCRIPT_SRC
    assert "Create a safe read-only project status inspection plan" in SCRIPT_SRC
    assert "redact" in SCRIPT_SRC
    # review-only: must not import an executor / repair / promotion runtime
    for forbidden in ("import execution_bridge", "from src.repair", "staging_promote",
                      "execute_plan", "build_execution_sequence"):
        assert forbidden not in SCRIPT_SRC, forbidden


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
