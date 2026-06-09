import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "approve_review_candidate.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
RUN_EVAL = ROOT / "scripts" / "run_eval.py"
EVAL = ROOT / "evals" / "planner" / "review_candidate_approval.yaml"
IMPORT_EVAL = ROOT / "evals" / "planner" / "review_package_import.yaml"
MS_EXEC_EVAL = ROOT / "evals" / "planner" / "openai_readonly_multistep_execution_gate.yaml"
EXAMPLE = ROOT / "reports" / "openai_multistep_plan_review_v0" / "example"
FAKE_KEY = "sk-" + "d" * 44

_spec = importlib.util.spec_from_file_location("approve_review_candidate", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

from src.planner.read_only_execution_gate import parse_approval  # noqa: E402

APPROVED_FILES = ("plan.json", "approval_checklist.md", "approval_report.json", "README.md")
REQUIRED_CRITERIA = [
    "candidate_loaded", "candidate_was_not_approved", "reviewer_checked", "plan_valid",
    "allowlisted_skills_only", "low_risk_only", "approved_fixture_created",
    "approval_marker_line_anchored", "plan_not_executed",
    "no_secret_in_approval_artifacts", "stable_safety_promotion_untouched", "score_1_0",
]


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def _eval(task):
    with tempfile.TemporaryDirectory() as tmp:
        return subprocess.run([sys.executable, str(RUN_EVAL), "--task", str(task),
                               "--runs-dir", tmp], capture_output=True, text=True, cwd=str(ROOT))


def test_script_and_eval_exist():
    assert SCRIPT.exists() and EVAL.exists() and (EXAMPLE / "plan.json").exists()


def test_allowlist_not_expanded():
    assert mod.APPROVE_ALLOWLIST == ("inspect_project", "list_project_files")


def test_dry_run_writes_nothing():
    r = _run(["--dry-run", "--candidate", str(EXAMPLE), "--output-id", "smoke"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["status"] == "DRY-RUN OK"
    assert data["candidate_was_not_approved"] is True
    assert not (ROOT / "fixtures" / "openai_planner" / "approved_imported_smoke").exists()


def test_default_is_dry_run():
    r = _run(["--candidate", str(EXAMPLE), "--output-id", "smoke"])
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["mode"] == "dry-run"


def test_approve_without_reviewer_rejected():
    r = _run(["--approve", "--candidate", str(EXAMPLE), "--output-id", "x"])
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert json.loads(r.stdout)["status"] == "BLOCKED"


def test_approve_with_placeholder_reviewer_rejected():
    for bad in ("TBD", "todo", "Unknown", "(none)", "  "):
        r = _run(["--approve", "--reviewer", bad, "--candidate", str(EXAMPLE), "--output-id", "x"])
        assert r.returncode == 1, (bad, r.stdout)


def test_approve_with_real_reviewer_writes_line_anchored_fixture():
    with tempfile.TemporaryDirectory() as tmp:
        r = _run(["--approve", "--reviewer", "alice", "--candidate", str(EXAMPLE),
                  "--output-id", "run1", "--out-base", tmp])
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data["status"] == "APPROVED"
        cand = Path(tmp) / "approved_imported_run1"
        for f in APPROVED_FILES:
            assert (cand / f).exists(), f
        chk = (cand / "approval_checklist.md").read_text(encoding="utf-8")
        # standalone line-anchored true marker; gate parses it as approved
        appr = parse_approval(chk)
        assert appr.approved_marker is True and appr.reviewer_ok is True
        assert data["approval_marker_line_anchored"] is True


def test_rejects_candidate_outside_allowed_source():
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "rogue"; pkg.mkdir()
        (pkg / "plan.json").write_text(json.dumps({"plan": {"goal": "g", "steps": [
            {"id": "a", "skill": "inspect_project", "risk_level": "low"}]}}), encoding="utf-8")
        r = _run(["--approve", "--reviewer", "alice", "--candidate", str(pkg), "--output-id", "x"])
        assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
        assert "BLOCKED" in json.loads(r.stdout)["status"]


def test_refuses_already_approved_candidate():
    # An already-approved fixture must not be re-approved.
    r = _run(["--approve", "--reviewer", "alice", "--candidate",
              "fixtures/openai_planner/approved_readonly_plan_multistep", "--output-id", "x"])
    # blocked either as not-an-allowed-source (2) or already-approved (1); both safe.
    assert r.returncode in (1, 2)


def test_imported_candidate_is_allowed_source():
    # Build an imported candidate, then confirm it is an allowed approval source.
    imp_spec = importlib.util.spec_from_file_location(
        "import_review_package", ROOT / "scripts" / "import_review_package.py")
    imp = importlib.util.module_from_spec(imp_spec); imp_spec.loader.exec_module(imp)
    with tempfile.TemporaryDirectory() as tmp:
        imp.build_import_candidate(EXAMPLE, Path(tmp) / "imported_review_package_abc",
                                   source_label=str(EXAMPLE))
        # path shape check via the approver's allow function (base override-free check
        # uses the real fixtures base, so emulate with an imported_* name under it)
    # The allow function accepts imported_review_package_* under fixtures/openai_planner.
    fake = ROOT / "fixtures" / "openai_planner" / "imported_review_package_xyz"
    assert mod.is_allowed_candidate(fake) is True
    assert mod.is_allowed_candidate(ROOT / "fixtures" / "openai_planner" / "approved_readonly_plan") is False


def test_no_secret_in_output_with_key_in_env():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    r = _run(["--dry-run", "--candidate", str(EXAMPLE), "--output-id", "smoke"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr


def test_script_safety_invariants_in_source():
    assert "--approve" in SCRIPT_SRC and "--dry-run" in SCRIPT_SRC and "--reviewer" in SCRIPT_SRC
    assert "redact" in SCRIPT_SRC
    for forbidden in ("execute_readonly_plan", "build_execution_sequence",
                      "from src.repair", "staging_promote", "build_provider",
                      "build_planner_from_config", "os.environ"):
        assert forbidden not in SCRIPT_SRC, forbidden


def test_approval_eval_scores_1_0():
    r = _eval(EVAL)
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "score=1.0" in r.stdout
    for c in REQUIRED_CRITERIA:
        assert f"[x] {c}" in r.stdout, c


def test_import_and_multistep_evals_still_1_0():
    for ev in (IMPORT_EVAL, MS_EXEC_EVAL):
        r = _eval(ev)
        assert r.returncode == 0, (ev, r.stdout, r.stderr)
        assert "score=1.0" in r.stdout


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
