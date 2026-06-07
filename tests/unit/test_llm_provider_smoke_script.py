import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "llm_provider_smoke.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
FAKE_KEY = "sk-" + "d" * 44


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_fake():
    r = _run(["--provider", "fake", "--dry-run"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["provider_name"] == "fake"
    assert data["real_api_enabled"] is False
    assert data["real_api_called"] is False
    assert data["redaction_ok"] is True


def test_dry_run_openai_constructs_no_call():
    r = _run(["--provider", "openai", "--dry-run"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["provider_name"] == "openai"
    assert data["real_api_enabled"] is True
    assert data["api_key_env"] == "OPENAI_API_KEY"   # NAME only
    assert data["real_api_called"] is False
    assert "DRY-RUN" in r.stderr


def test_dry_run_anthropic_constructs_no_call():
    r = _run(["--provider", "anthropic", "--dry-run"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["provider_name"] == "anthropic"
    assert data["api_key_env"] == "ANTHROPIC_API_KEY"
    assert data["real_api_called"] is False


def test_default_is_dry_run_no_call():
    # no --dry-run and no --real-call => still no real call
    r = _run(["--provider", "openai"])
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["real_api_called"] is False


def test_real_call_fake_blocked():
    r = _run(["--provider", "fake", "--real-call"])
    assert r.returncode != 0
    assert "not applicable to the fake provider" in r.stderr.lower()


def test_real_call_blocked_without_allow_flag():
    # config.json default has allow_real_api_calls=false (or absent) -> fail closed.
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY  # key present but not allowed => still blocked
    r = _run(["--provider", "openai", "--real-call"], env=env)
    assert r.returncode == 2
    assert "blocked" in r.stderr.lower()
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr


def test_no_secret_in_output_even_with_env_keys():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    env["ANTHROPIC_API_KEY"] = "sk-ant-" + "e" * 40
    for prov in ("fake", "openai", "anthropic"):
        r = _run(["--provider", prov, "--dry-run"], env=env)
        assert r.returncode == 0, r.stderr
        assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
        assert ("sk-ant-" + "e" * 40) not in r.stdout


def test_script_default_safe_no_real_call_token():
    # the script never makes a real call by default; --real-call is opt-in only
    assert "--real-call" in SCRIPT_SRC
    assert "fail closed" in SCRIPT_SRC.lower() or "blocked" in SCRIPT_SRC.lower()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
