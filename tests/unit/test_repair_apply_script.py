import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "repair_apply.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
FIXTURE_WS = ROOT / "fixtures" / "repair" / "fake_approved_proposal_workspace"
FAKE_KEY = "sk-" + "s" * 40
EXPECTED_ALLOWLIST = (
    "python scripts/validate_structure.py",
    "python scripts/validate_workflows.py",
    "python scripts/run_unit_tests.py",
    "python scripts/run_demo.py --demo vite_login_bug",
)


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_does_not_create_apply_workspace():
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--proposal-workspace", str(FIXTURE_WS), "--dry-run", "--output", d])
        assert r.returncode == 0, r.stderr
        assert "DRY-RUN" in r.stderr
        assert "[WROTE]" not in r.stderr
        # no workspace created
        assert not any(Path(d).iterdir())


def test_no_approved_rejected():
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--proposal-workspace", str(FIXTURE_WS), "--apply-id", "x", "--output", d])
        assert r.returncode != 0
        assert "REJECTED" in r.stderr
        assert not any(Path(d).iterdir())


def test_approved_creates_apply_workspace():
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--proposal-workspace", str(FIXTURE_WS), "--approved",
                  "--apply-id", "fake_apply", "--output", d])
        assert r.returncode == 0, r.stderr
        assert "[WROTE]" in r.stderr
        ws = Path(d) / "fake_apply"
        for f in ("apply_manifest.json", "apply_report.md", "test_results.json"):
            assert (ws / f).exists(), f
        manifest = json.loads((ws / "apply_manifest.json").read_text(encoding="utf-8"))
        assert manifest["promoted"] is False
        assert manifest["stable_modified"] is False


def test_test_commands_are_fixed_allowlist():
    from src.repair.patch_application import ALLOWLISTED_TEST_COMMANDS
    assert tuple(ALLOWLISTED_TEST_COMMANDS) == EXPECTED_ALLOWLIST
    # the manifest test_commands come from the constant, not the proposal
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--proposal-workspace", str(FIXTURE_WS), "--approved",
                  "--apply-id", "fa", "--output", d])
        assert r.returncode == 0, r.stderr
        manifest = json.loads((Path(d) / "fa" / "apply_manifest.json").read_text(encoding="utf-8"))
        assert manifest["test_commands"] == list(EXPECTED_ALLOWLIST)


def test_no_stable_files_modified():
    # the script writes only under --output; no skills/ or safety_gate file changes
    skills_dir = ROOT / "skills"
    before = sorted(p.name for p in skills_dir.iterdir()) if skills_dir.exists() else []
    with tempfile.TemporaryDirectory() as d:
        _run(["--proposal-workspace", str(FIXTURE_WS), "--approved", "--apply-id", "z", "--output", d])
    after = sorted(p.name for p in skills_dir.iterdir()) if skills_dir.exists() else []
    assert before == after
    # the script body never opens a raw shell
    assert "shell=True" not in SCRIPT_SRC
    assert "os.system" not in SCRIPT_SRC


def test_no_secret_in_apply_report():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--proposal-workspace", str(FIXTURE_WS), "--approved",
                  "--apply-id", "s", "--output", d], env=env)
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
