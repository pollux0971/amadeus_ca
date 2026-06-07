"""Unit tests for scripts/planner_provider_smoke.py (dry-run; plan-only; no real API)."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "planner_provider_smoke.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
FAKE_KEY = "sk-" + "s" * 44


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def _summary(stdout):
    # stdout is the redacted JSON summary (a single object).
    return json.loads(stdout)


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_fake():
    r = _run(["--provider", "fake", "--dry-run"])
    assert r.returncode == 0, r.stderr
    data = _summary(r.stdout)
    assert data["provider_name"] == "fake"
    assert data["real_api_enabled"] is False
    assert data["real_api_called"] is False
    assert data["plan_executed"] is False
    assert data["fake_default_confirmed"] is True
    assert data["plan_created"] is True and data["plan_valid"] is True
    assert data["no_secret_in_plan"] is True and data["redaction_ok"] is True


def test_dry_run_openai_constructs_held_no_call():
    r = _run(["--provider", "openai", "--dry-run"])
    assert r.returncode == 0, r.stderr
    data = _summary(r.stdout)
    assert data["provider_name"] == "openai"
    assert data["real_api_enabled"] is True
    assert data["real_provider_blocked_without_opt_in"] is True
    assert data["real_api_called"] is False  # held, never called
    assert data["plan_executed"] is False
    assert data["plan_created"] is True and data["plan_valid"] is True


def test_dry_run_anthropic_constructs_held_no_call():
    r = _run(["--provider", "anthropic", "--dry-run"])
    assert r.returncode == 0, r.stderr
    data = _summary(r.stdout)
    assert data["provider_name"] == "anthropic"
    assert data["real_api_enabled"] is True
    assert data["real_provider_blocked_without_opt_in"] is True
    assert data["real_api_called"] is False


def test_no_secret_leaks_with_key_in_env():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    env["ANTHROPIC_API_KEY"] = "sk-ant-" + "t" * 40
    r = _run(["--provider", "openai", "--dry-run"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr


def test_script_has_no_real_call_flag():
    # The smoke script is dry-run only — it must not expose a real-call path.
    assert "--real-call" not in SCRIPT_SRC
    assert "real_call=True" not in SCRIPT_SRC
    # It does not read an env-var VALUE itself.
    assert "os.environ" not in SCRIPT_SRC and "getenv" not in SCRIPT_SRC


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
