import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "real_provider_live_smoke.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
# A fake key value built at runtime — never a real secret; only used to prove it is
# never echoed and that presence-without-opt-in still does not call the network.
FAKE_KEY = "sk-" + "d" * 44


def _run(args, env=None):
    # Always write reports into a throwaway dir so tests never touch runs/.
    with tempfile.TemporaryDirectory() as tmp:
        full = [*args, "--out-dir", tmp]
        r = subprocess.run([sys.executable, str(SCRIPT), *full], capture_output=True,
                           text=True, cwd=str(ROOT), env=env)
        reports = {}
        jp = Path(tmp) / "live_smoke_report.json"
        mp = Path(tmp) / "live_smoke_report.md"
        if jp.exists():
            reports["json_text"] = jp.read_text(encoding="utf-8")
            reports["json"] = json.loads(reports["json_text"])
        if mp.exists():
            reports["md"] = mp.read_text(encoding="utf-8")
    return r, reports


def _env_without_key():
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def test_script_exists():
    assert SCRIPT.exists()


def test_dry_run_openai_constructs_no_call():
    r, reports = _run(["--provider", "openai", "--dry-run"], env=_env_without_key())
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["provider_requested"] == "openai"
    assert data["mode"] == "dry-run"
    assert data["api_key_env"] == "OPENAI_API_KEY"      # NAME only
    assert data["constructed"] is True
    assert data["real_api_called"] is False
    assert data["redaction_ok"] is True
    assert data["config_ok"] is True
    assert data["fixed_prompt"] == "Reply with exactly: provider-ok"
    assert "DRY-RUN" in r.stderr
    # reports written and redacted, no secret
    assert reports["json"]["real_api_called"] is False
    assert "provider-ok" in reports["md"]


def test_default_is_dry_run_no_call():
    # no --dry-run and no --real-call => still no real call
    r, _ = _run(["--provider", "openai"], env=_env_without_key())
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["real_api_called"] is False


def test_real_call_blocked_without_key():
    # No OPENAI_API_KEY in the environment => fail closed, exit 2 BLOCKED.
    r, reports = _run(["--provider", "openai", "--real-call"], env=_env_without_key())
    assert r.returncode == 2, r.stderr
    assert "blocked" in r.stderr.lower()
    assert "BLOCKED" in json.loads(r.stdout)["status"]
    assert reports["json"]["real_api_called"] is False


def test_anthropic_real_call_blocked_not_tested():
    # Anthropic stays blocked / not tested this round, even if a key is present.
    env = _env_without_key()
    env["ANTHROPIC_API_KEY"] = "sk-ant-" + "e" * 40
    r, reports = _run(["--provider", "anthropic", "--real-call"], env=env)
    assert r.returncode == 2, r.stderr
    assert "openai only" in r.stderr.lower() or "not supported" in r.stderr.lower()
    assert reports["json"]["real_api_called"] is False
    # the anthropic key value must never appear
    assert ("sk-ant-" + "e" * 40) not in r.stdout
    assert ("sk-ant-" + "e" * 40) not in reports["json_text"]


def test_no_secret_in_output_even_with_env_key():
    # A key present but no opt-in => still no call, and the value is never echoed.
    env = _env_without_key()
    env["OPENAI_API_KEY"] = FAKE_KEY
    r, reports = _run(["--provider", "openai", "--dry-run"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
    assert FAKE_KEY not in reports["json_text"]
    assert FAKE_KEY not in reports["md"]
    # presence is reported as a boolean only
    assert json.loads(r.stdout)["env_var_present"] is True


def test_bad_api_key_env_name_blocked():
    r, _ = _run(["--provider", "openai", "--api-key-env", "lower-case"],
                env=_env_without_key())
    assert r.returncode == 2
    assert "blocked" in r.stderr.lower()


def test_script_safety_invariants_in_source():
    # The script must default safe and gate the real call; never read a secret file.
    assert "--real-call" in SCRIPT_SRC
    assert "--dry-run" in SCRIPT_SRC
    assert "fail closed" in SCRIPT_SRC.lower() or "fail-closed" in SCRIPT_SRC.lower()
    assert "Reply with exactly: provider-ok" in SCRIPT_SRC
    # the key is read only from the named env var, never opened from a local file
    assert "os.environ.get(api_key_env)" in SCRIPT_SRC
    assert "open(" not in SCRIPT_SRC  # no local file open of secrets/.env


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
