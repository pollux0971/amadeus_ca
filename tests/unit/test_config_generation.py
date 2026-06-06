import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

GEN = ROOT / "scripts" / "generate_config.py"
_spec = importlib.util.spec_from_file_location("generate_config_under_test", GEN)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

# Fake key built at runtime so this test file never contains a real one.
FAKE_KEY = "sk-" + "x" * 40


def _gen(args, env=None):
    return subprocess.run([sys.executable, str(GEN), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_dry_run_writes_nothing():
    with tempfile.TemporaryDirectory() as d:
        out = str(Path(d) / "c.json")
        r = _gen(["--provider", "fake", "--output", out, "--dry-run"])
        assert r.returncode == 0
        assert not Path(out).exists()
        # default (no --write) is also dry-run
        r2 = _gen(["--provider", "fake", "--output", out])
        assert r2.returncode == 0 and not Path(out).exists()


def test_write_creates_config():
    with tempfile.TemporaryDirectory() as d:
        out = str(Path(d) / "config.json")
        r = _gen(["--provider", "fake", "--output", out, "--write"])
        assert r.returncode == 0, r.stderr
        assert Path(out).exists()
        cfg = json.loads(Path(out).read_text(encoding="utf-8"))
        assert cfg["llm"]["provider"] == "fake"


def test_fake_provider_is_safe_by_default():
    cfg = mod.build_config("default", "local", "fake", "", enable_real_api=False)
    llm = cfg["llm"]
    assert llm["provider"] == "fake"
    assert llm["api_key_env"] is None
    assert llm["enabled"] is False
    assert llm["allow_real_api_calls"] is False
    assert llm["redact_secrets"] is True
    assert llm["fail_closed"] is True


def test_openai_records_env_name_only():
    cfg = mod.build_config("default", "local", "openai", "", enable_real_api=True)
    assert cfg["llm"]["api_key_env"] == "OPENAI_API_KEY"
    # no key value anywhere
    text = json.dumps(cfg)
    for rx in _key_patterns().values():
        assert rx.search(text) is None


def test_anthropic_records_env_name_only():
    cfg = mod.build_config("default", "local", "anthropic", "", enable_real_api=True)
    assert cfg["llm"]["api_key_env"] == "ANTHROPIC_API_KEY"


def test_enable_real_api_never_reads_or_outputs_env_value():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY  # a value the generator must NOT read/echo
    with tempfile.TemporaryDirectory() as d:
        out = str(Path(d) / "config.json")
        r = _gen(["--provider", "openai", "--enable-real-api", "--output", out, "--write"], env=env)
        assert r.returncode == 0, r.stderr
        # the value must not appear in stdout/stderr ...
        assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
        # ... nor in the written file (only the env var NAME is recorded)
        content = Path(out).read_text(encoding="utf-8")
        assert FAKE_KEY not in content
        cfg = json.loads(content)
        assert cfg["llm"]["api_key_env"] == "OPENAI_API_KEY"
        assert cfg["llm"]["allow_real_api_calls"] is True


def test_generated_config_has_no_secret_pattern():
    with tempfile.TemporaryDirectory() as d:
        out = str(Path(d) / "config.json")
        _gen(["--provider", "openai", "--enable-real-api", "--output", out, "--write"])
        text = Path(out).read_text(encoding="utf-8")
        for rx in _key_patterns().values():
            assert rx.search(text) is None


def test_config_json_is_gitignored():
    r = subprocess.run(["git", "check-ignore", "-q", "config/config.json"], cwd=str(ROOT))
    assert r.returncode == 0, "config/config.json must be gitignored"


def test_refuses_to_overwrite_protected_example():
    r = _gen(["--provider", "fake", "--output", "config/config.example.json", "--write"])
    assert r.returncode == 2
    assert "REFUSED" in r.stdout


def _key_patterns():
    spec = importlib.util.spec_from_file_location("csh_t", ROOT / "scripts" / "check_secret_hygiene.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.KEY_PATTERNS


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
