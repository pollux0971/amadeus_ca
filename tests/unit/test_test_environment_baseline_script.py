import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "check_test_environment_baseline.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("check_test_environment_baseline", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

# A synthetic secret-looking value placed in the environment to prove the checker
# never echoes env values. Never a real key.
FAKE_KEY = "sk-" + "b" * 44


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_exists():
    assert SCRIPT.exists()


def test_default_report_exits_zero():
    r = _run([])
    assert r.returncode == 0, r.stderr
    assert "Test Environment Baseline" in r.stdout


def test_json_mode_is_valid_and_has_summary():
    r = _run(["--json"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert "summary" in data and "warnings" in data
    s = data["summary"]
    assert "venv_python_exists" in s
    assert "real_browser_path_available" in s
    assert "python_on_path" in s
    assert isinstance(s["known_env_gap_tests"], list) and s["known_env_gap_tests"]


def test_python_not_on_path_is_warning_not_failure():
    # Force an empty PATH so `python` cannot be found; the checker must still exit 0
    # and report it as a warning (never a failure).
    env = dict(os.environ)
    env["PATH"] = ""
    r = _run([], env=env)
    assert r.returncode == 0, r.stderr
    assert mod.gather(ROOT) is not None  # gather never raises
    # The summary reflects python-not-on-PATH without failing.
    rj = _run(["--json"], env=env)
    assert rj.returncode == 0
    assert json.loads(rj.stdout)["summary"]["python_on_path"] is False


def test_gather_marks_known_env_gap_tests():
    s = mod.gather(ROOT)
    assert s["known_env_gap_tests"] == mod.KNOWN_ENV_GAP_TESTS
    assert any("test_browser_keep_alive_e2e" in t for t in s["known_env_gap_tests"])
    assert any("test_missing_prereqs_block_with_exit_2" in t for t in s["known_env_gap_tests"])


def test_require_real_browser_flag_blocks_only_when_unavailable():
    # In THIS environment the .venv real-browser path is available, so even with the
    # strict flag the checker should pass. (We assert it does not crash and the exit
    # code matches the availability the checker itself reports.)
    s = mod.gather(ROOT)
    r = _run(["--require-real-browser"])
    if s["real_browser_path_available"]:
        assert r.returncode == 0, r.stderr
    else:
        assert r.returncode == 2


def test_script_does_not_install_or_download():
    for forbidden in ("pip install", "playwright install", "urllib.request",
                      "urlopen", "subprocess.run([\"pip", "os.system"):
        assert forbidden not in SCRIPT_SRC, forbidden


def test_script_reads_no_secret_and_emits_no_env_value():
    # Even with secret-looking env values set, the output contains no key value.
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    env["ANTHROPIC_API_KEY"] = "sk-ant-" + "c" * 40
    r = _run(["--json"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
    assert ("sk-ant-" + "c" * 40) not in r.stdout
    # the script must not OPEN a local secret file (docstring may mention .env /
    # password_and_api.txt only to say it reads neither — so check behavior, not text):
    # it performs no file open at all beyond importlib/subprocess.
    assert "open(" not in SCRIPT_SRC
    assert "read_text(" not in SCRIPT_SRC


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
