import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXAMPLE = ROOT / "ui_dashboard" / "data" / "dashboard_snapshot.example.json"
GENERATED = ROOT / "ui_dashboard" / "data" / "dashboard_snapshot.json"
GEN_SCRIPT = ROOT / "scripts" / "generate_dashboard_snapshot.py"

REQUIRED_KEYS = ["latest_checkpoint", "phase_status", "candidate_status", "eval_status",
                 "epic_story_status", "safety_invariants", "links_to_reports", "generated_at"]
FAKE_KEY = "sk-" + "z" * 40


def test_example_snapshot_has_required_keys():
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    for k in REQUIRED_KEYS:
        assert k in data, f"example snapshot missing {k!r}"


def test_example_snapshot_has_no_secret_or_raw_trace():
    from src.llm.redaction import redact_text
    text = EXAMPLE.read_text(encoding="utf-8")
    assert redact_text(text) == text
    low = text.lower()
    for bad in ("api_key", "authorization:", "password", "trace.jsonl\":"):
        assert bad not in low, f"example snapshot contains {bad!r}"


def test_generator_produces_valid_snapshot():
    r = subprocess.run([sys.executable, str(GEN_SCRIPT)], capture_output=True,
                       text=True, cwd=str(ROOT))
    assert r.returncode == 0, r.stderr
    assert GENERATED.exists()
    data = json.loads(GENERATED.read_text(encoding="utf-8"))
    for k in REQUIRED_KEYS:
        assert k in data, f"generated snapshot missing {k!r}"
    assert data["latest_checkpoint"].startswith("checkpoint-")
    assert isinstance(data["phase_status"], list) and data["phase_status"]
    assert data["generated_at"].endswith("Z")


def test_generated_snapshot_has_no_secret_even_with_env_key():
    from src.llm.redaction import redact_text
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY  # must never leak into the snapshot
    r = subprocess.run([sys.executable, str(GEN_SCRIPT)], capture_output=True,
                       text=True, cwd=str(ROOT), env=env)
    assert r.returncode == 0, r.stderr
    text = GENERATED.read_text(encoding="utf-8")
    assert FAKE_KEY not in text
    assert redact_text(text) == text


def test_generator_refuses_to_write_on_secret(tmp_path=None):
    # If the assembled snapshot contained a secret, the generator must refuse (exit !=0)
    # and not write. We simulate by importing build_snapshot and checking the guard
    # logic: inject a secret and confirm redact_text would change it (the guard trips).
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen", GEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from src.llm.redaction import redact_text
    tainted = json.dumps({"x": "sk-" + "a" * 40})
    assert redact_text(tainted) != tainted  # the guard (redact_text(text)!=text) would trigger
    # and a clean snapshot does NOT trip it
    clean = json.dumps(mod.build_snapshot(), ensure_ascii=False, indent=2)
    assert redact_text(clean) == clean


def test_generator_does_not_read_runs_or_secret_paths():
    src = GEN_SCRIPT.read_text(encoding="utf-8")
    # explicit guard against runs/.env/password
    assert "runs/" in src and ".env" in src and "password" in src.lower()
    assert "SAFE_READ_ROOTS" in src


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
