import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "plan_task.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
FAKE_KEY = "sk-" + "c" * 40


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_plan_command_works():
    r = _run(["--goal", "FAKE_PLAN_FULL_BROWSER_E2E", "--marker", "FAKE_PLAN_FULL_BROWSER_E2E"])
    assert r.returncode == 0, r.stderr
    assert "# Plan" in r.stdout
    assert "start_local_server" in r.stdout
    # plan-only: nothing was written by default
    assert "[WROTE]" not in r.stderr


def test_json_works():
    r = _run(["--goal", "g", "--marker", "FAKE_PLAN_INSPECT_PROJECT", "--json"])
    assert r.returncode == 0, r.stderr
    doc = json.loads(r.stdout)
    assert doc["plan"]["steps"][0]["skill"] == "inspect_project"
    assert doc["validation"]["valid"] is True


def test_write_writes_plan_file():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "plan.json"
        r = _run(["--goal", "g", "--marker", "FAKE_PLAN_PATCH_ONLY",
                  "--write", str(out)])
        assert r.returncode == 0, r.stderr
        assert out.exists()
        doc = json.loads(out.read_text(encoding="utf-8"))
        assert "patch_file_and_run_tests" in [s["skill"] for s in doc["plan"]["steps"]]


def test_written_plan_contains_no_secret():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    env["ANTHROPIC_API_KEY"] = "sk-ant-" + "d" * 40
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "plan.json"
        r = _run(["--goal", f"leak {FAKE_KEY}", "--marker", "FAKE_PLAN_FULL_BROWSER_E2E",
                  "--write", str(out)], env=env)
        assert r.returncode == 0, r.stderr
        text = out.read_text(encoding="utf-8")
        assert FAKE_KEY not in text
        assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr


def test_script_does_not_execute_skills():
    # source must not import or call the skill executor / subprocess for skills
    assert "SkillExecutor" not in SCRIPT_SRC
    assert "executor.run" not in SCRIPT_SRC
    # functional: a full-browser plan request starts no server / browser — it
    # returns instantly with a plan and writes nothing unless asked.
    r = _run(["--goal", "FAKE_PLAN_FULL_BROWSER_E2E", "--marker", "FAKE_PLAN_FULL_BROWSER_E2E"])
    assert r.returncode == 0
    assert "server_url" not in r.stdout  # no real server was started


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
