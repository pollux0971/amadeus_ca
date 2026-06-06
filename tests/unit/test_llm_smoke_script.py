import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "llm_smoke.py"
FAKE_KEY = "sk-" + "w" * 40


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_exists():
    assert SCRIPT.exists()


def test_fake_only_outputs_fake_provider():
    r = _run(["--fake-only"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["provider"] == "fake"
    assert data["real_api_enabled"] is False


def test_output_contains_no_secret_even_with_env_key_set():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    env["ANTHROPIC_API_KEY"] = "sk-ant-" + "v" * 40
    r = _run(["--fake-only", "--marker", "FAKE_PLAN_FULL_BROWSER_E2E"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and "sk-ant-" + "v" * 40 not in r.stdout
    # no key prefix leaked
    assert "sk-" + "w" * 40 not in r.stdout


def test_marker_returns_plan():
    r = _run(["--fake-only", "--marker", "FAKE_PLAN_INSPECT_PROJECT"])
    data = json.loads(r.stdout)
    assert data["response"]["decision"] == "plan"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
