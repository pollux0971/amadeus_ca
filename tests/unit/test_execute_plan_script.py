import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "execute_plan.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
FAKE_KEY = "sk-" + "f" * 40


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_does_not_execute():
    r = _run(["--goal", "FAKE_PLAN_FULL_BROWSER_E2E", "--marker",
              "FAKE_PLAN_FULL_BROWSER_E2E", "--dry-run"])
    assert r.returncode == 0, r.stderr
    assert "executable sequence" in r.stdout
    assert "DRY-RUN" in r.stderr
    # nothing executed: no PASS/FAIL execution line, no server output
    assert "[PASS] execute" not in r.stderr and "[FAIL] execute" not in r.stderr


def test_marker_full_browser_plan_can_dry_run():
    r = _run(["--marker", "FAKE_PLAN_FULL_BROWSER_E2E", "--dry-run"])
    assert r.returncode == 0, r.stderr
    for skill in ("start_local_server", "open_localhost_browser",
                  "read_browser_console", "patch_file_and_run_tests"):
        assert skill in r.stdout


def test_unknown_skill_exits_nonzero():
    # a marker with no vetted execution context fails closed on --execute
    r = _run(["--marker", "FAKE_PLAN_INSPECT_PROJECT", "--execute"])
    assert r.returncode != 0
    assert "BLOCKED" in r.stderr


def test_execute_requires_validation_pass(tmp_path=None):
    # Hand-craft a plan.json with a duplicate id (invalid) and try to execute it.
    bad_plan = {"plan": {"goal": "g", "marker": "FAKE_PLAN_PATCH_ONLY", "steps": [
        {"id": "dup", "skill": "inspect_project", "inputs": {}, "expected_outputs": [],
         "success_criteria": [], "risk_level": "low", "requires_approval": False, "depends_on": []},
        {"id": "dup", "skill": "patch_file_and_run_tests", "inputs": {}, "expected_outputs": [],
         "success_criteria": [], "risk_level": "low", "requires_approval": False, "depends_on": []},
    ]}}
    p = ROOT / "runs" / "_test_bad_plan.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(bad_plan), encoding="utf-8")
    try:
        r = _run(["--plan", str(p), "--execute"])
        assert r.returncode != 0
        assert "BLOCKED" in r.stderr
    finally:
        p.unlink(missing_ok=True)


def test_patch_only_plan_can_execute_in_controlled_fixture():
    r = _run(["--marker", "FAKE_PLAN_PATCH_ONLY", "--execute"])
    assert r.returncode == 0, r.stderr
    assert "[PASS] execute FAKE_PLAN_PATCH_ONLY" in r.stderr
    assert "score=1.0" in r.stderr


def test_writes_redacted_artifacts_no_secret():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    env["ANTHROPIC_API_KEY"] = "sk-ant-" + "g" * 40
    r = _run(["--goal", f"leak {FAKE_KEY}", "--marker", "FAKE_PLAN_PATCH_ONLY", "--execute"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
    # locate the run dir and scan every text artifact
    run_dir = None
    for line in r.stderr.splitlines():
        if "run=" in line:
            run_dir = Path(line.split("run=", 1)[1].strip())
    assert run_dir and run_dir.exists()
    for f in run_dir.rglob("*"):
        if f.is_file() and f.suffix not in (".png", ".jpg"):
            try:
                assert FAKE_KEY not in f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                pass


def test_script_does_no_direct_shell_or_llm():
    # The script never opens a raw shell or calls a real provider.
    for needle in ("os.system", "subprocess.Popen", "openai", "anthropic", "real_api"):
        assert needle not in SCRIPT_SRC, needle


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
