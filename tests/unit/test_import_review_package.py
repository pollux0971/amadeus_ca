import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "import_review_package.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
RUN_EVAL = ROOT / "scripts" / "run_eval.py"
EVAL = ROOT / "evals" / "planner" / "review_package_import.yaml"
MS_EXEC_EVAL = ROOT / "evals" / "planner" / "openai_readonly_multistep_execution_gate.yaml"
EXAMPLE_PKG = ROOT / "reports" / "openai_multistep_plan_review_v0" / "example"
FAKE_KEY = "sk-" + "d" * 44

_spec = importlib.util.spec_from_file_location("import_review_package", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

CANDIDATE_FILES = ("plan.json", "plan_summary.md", "approval_checklist.md",
                   "import_report.json", "README.md")
REQUIRED_CRITERIA = [
    "review_package_loaded", "plan_valid", "allowlisted_skills_only", "low_risk_only",
    "fixture_candidate_created", "approval_not_granted", "plan_not_executed",
    "no_secret_in_import_artifacts", "stable_safety_promotion_untouched", "score_1_0",
]


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_and_eval_and_example_exist():
    assert SCRIPT.exists() and EVAL.exists()
    assert (EXAMPLE_PKG / "plan.json").exists()


def test_import_allowlist_not_expanded():
    assert mod.IMPORT_ALLOWLIST == ("inspect_project", "list_project_files")


def test_dry_run_validates_writes_nothing():
    r = _run(["--dry-run", "--review-package", str(EXAMPLE_PKG)])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["mode"] == "dry-run"
    assert data["status"] == "DRY-RUN OK"
    assert data["importable"] is True
    assert data["allowlisted_skills_only"] is True and data["low_risk_only"] is True
    assert data["approved_for_readonly_execution"] is False
    # nothing written to the real fixtures tree
    assert not (ROOT / "fixtures" / "openai_planner" /
                f"imported_review_package_{data['candidate_id']}").exists()


def test_default_is_dry_run():
    r = _run(["--review-package", str(EXAMPLE_PKG)])
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["mode"] == "dry-run"


def test_write_creates_not_approved_candidate():
    with tempfile.TemporaryDirectory() as tmp:
        r = _run(["--write", "--review-package", str(EXAMPLE_PKG), "--out-base", tmp])
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        cand = Path(tmp) / f"imported_review_package_{data['candidate_id']}"
        assert cand.exists()
        for f in CANDIDATE_FILES:
            assert (cand / f).exists(), f
        chk = (cand / "approval_checklist.md").read_text(encoding="utf-8")
        assert "APPROVED_FOR_READONLY_EXECUTION: false" in chk
        # The gate must parse this NOT-APPROVED checklist as un-approved even though the
        # help text mentions the true marker (line-anchored parse, not substring).
        from src.planner.read_only_execution_gate import parse_approval
        assert parse_approval(chk).approved_marker is False
        rep = json.loads((cand / "import_report.json").read_text(encoding="utf-8"))
        assert rep["approved_for_readonly_execution"] is False
        assert rep["plan_executed"] is False


def test_generated_checklist_is_not_approved_per_gate():
    # The generated approval checklist (and the openai_plan_review one) must parse as
    # NOT approved by the gate — the help text may mention the marker, but only a
    # standalone marker LINE grants approval.
    from src.planner.read_only_execution_gate import parse_approval
    md = mod._approval_md()
    assert "APPROVED_FOR_READONLY_EXECUTION: false" in md
    assert parse_approval(md).approved_marker is False


def test_blocks_non_allowlisted_or_high_risk_plan():
    # Build a review package whose plan has a forbidden skill -> not importable.
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "pkg"; pkg.mkdir()
        (pkg / "plan.json").write_text(json.dumps({"plan": {"goal": "g", "steps": [
            {"id": "a", "skill": "patch_file_and_run_tests", "risk_level": "low"}]}}),
            encoding="utf-8")
        r = _run(["--write", "--review-package", str(pkg), "--out-base", tmp])
        assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
        assert json.loads(r.stdout)["status"] == "BLOCKED"


def test_missing_plan_json_fails_closed():
    with tempfile.TemporaryDirectory() as tmp:
        r = _run(["--dry-run", "--review-package", tmp])
        assert r.returncode == 2


def test_no_secret_in_output_with_key_in_env():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    r = _run(["--dry-run", "--review-package", str(EXAMPLE_PKG)], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr


def test_script_safety_invariants_in_source():
    assert "--write" in SCRIPT_SRC and "--dry-run" in SCRIPT_SRC
    assert "redact" in SCRIPT_SRC
    # import-only: must not execute / repair / promote / call OpenAI
    for forbidden in ("execute_readonly_plan", "build_execution_sequence",
                      "from src.repair", "staging_promote", "build_provider",
                      "build_planner_from_config", "os.environ.get"):
        assert forbidden not in SCRIPT_SRC, forbidden


def test_import_eval_scores_1_0():
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
