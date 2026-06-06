import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "staging_promote.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
FIXTURE = ROOT / "fixtures" / "repair" / "fake_approved_merge_workspace"
FAKE_KEY = "sk-" + "z" * 40
EXPECTED_ALLOWLIST = (
    "python scripts/validate_structure.py",
    "python scripts/validate_workflows.py",
    "python scripts/run_unit_tests.py",
    "python scripts/run_demo.py --demo vite_login_bug",
    "python scripts/run_eval.py --task evals/repair/fake_candidate_merge.yaml",
    "python scripts/run_eval.py --task evals/repair/fake_approved_patch_application.yaml",
    "python scripts/run_eval.py --task evals/repair/fake_repair_proposal_only.yaml",
    "python scripts/run_eval.py --task evals/planner/fake_full_browser_plan_execution.yaml",
)


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_does_not_create_staging_workspace():
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--merge-workspace", str(FIXTURE), "--dry-run", "--output", d])
        assert r.returncode == 0, r.stderr
        assert "DRY-RUN" in r.stderr
        assert "[WROTE]" not in r.stderr
        assert not any(Path(d).iterdir())


def test_no_approved_rejected():
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--merge-workspace", str(FIXTURE), "--reviewer", "operator",
                  "--staging-id", "x", "--output", d])
        assert r.returncode != 0
        assert "REJECTED" in r.stderr
        assert not any(Path(d).iterdir())


def test_empty_reviewer_rejected():
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--merge-workspace", str(FIXTURE), "--approved",
                  "--staging-id", "x", "--output", d])
        assert r.returncode != 0
        assert "REJECTED" in r.stderr
        assert not any(Path(d).iterdir())


def test_approved_creates_staging_workspace():
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--merge-workspace", str(FIXTURE), "--approved", "--reviewer", "operator",
                  "--staging-id", "fake_staging", "--output", d])
        assert r.returncode == 0, r.stderr
        assert "[WROTE]" in r.stderr
        ws = Path(d) / "fake_staging"
        for f in ("staging_manifest.json", "staging_report.md", "rollback_verification.md",
                  "regression_results.json", "stable_promotion_checklist.md"):
            assert (ws / f).exists(), f
        manifest = json.loads((ws / "staging_manifest.json").read_text(encoding="utf-8"))
        assert manifest["stable_promoted"] is False
        assert manifest["stable_modified"] is False
        assert manifest["active_candidate_modified"] is False
        assert manifest["staged"] is True


def test_test_commands_are_fixed_allowlist():
    from src.repair.staging_promotion import STAGING_TEST_COMMANDS
    assert tuple(STAGING_TEST_COMMANDS) == EXPECTED_ALLOWLIST
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--merge-workspace", str(FIXTURE), "--approved", "--reviewer", "op",
                  "--staging-id", "fa", "--output", d])
        assert r.returncode == 0, r.stderr
        rr = json.loads((Path(d) / "fa" / "regression_results.json").read_text(encoding="utf-8"))
        assert rr["commands"] == list(EXPECTED_ALLOWLIST)


def test_no_stable_or_active_candidate_modified():
    skills_dir = ROOT / "skills"
    before = sorted(p.name for p in skills_dir.iterdir()) if skills_dir.exists() else []
    cand_dir = ROOT / "harnesses" / "candidates"
    cand_before = sorted(p.name for p in cand_dir.iterdir()) if cand_dir.exists() else []
    with tempfile.TemporaryDirectory() as d:
        _run(["--merge-workspace", str(FIXTURE), "--approved", "--reviewer", "op",
              "--staging-id", "z", "--output", d])
    after = sorted(p.name for p in skills_dir.iterdir()) if skills_dir.exists() else []
    cand_after = sorted(p.name for p in cand_dir.iterdir()) if cand_dir.exists() else []
    assert before == after
    assert cand_before == cand_after  # no active candidate added/changed
    assert "shell=True" not in SCRIPT_SRC
    assert "os.system" not in SCRIPT_SRC


def test_no_secret_in_staging_report():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--merge-workspace", str(FIXTURE), "--approved", "--reviewer", "op",
                  "--staging-id", "s", "--output", d], env=env)
        assert r.returncode == 0, r.stderr
        assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
        for f in (Path(d) / "s").rglob("*"):
            if f.is_file():
                try:
                    assert FAKE_KEY not in f.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    pass


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
