import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "repair_propose.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
FIXTURE = ROOT / "fixtures" / "repair" / "fake_failed_eval"
REPORT = FIXTURE / "summary.md"
FAKE_KEY = "sk-" + "m" * 40


def _run(args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(ROOT), env=env)


def test_script_exists_and_propose_stays_proposal_only():
    assert SCRIPT.exists()
    # repair_propose.py itself stays proposal-only: its --apply is rejected
    # (Phase 4's separate, human-approved repair_apply.py owns the apply path).
    assert "--apply" in SCRIPT_SRC
    assert "def apply" not in SCRIPT_SRC


def test_dry_run_works_and_writes_nothing():
    r = _run(["--failure-report", str(REPORT), "--marker", "FAKE_REPAIR_TEST_FAILED", "--dry-run"])
    assert r.returncode == 0, r.stderr
    assert "Repair Proposal" in r.stdout
    assert "PROPOSAL ONLY" in r.stdout
    assert "DRY-RUN" in r.stderr
    assert "[WROTE]" not in r.stderr


def test_proposal_output_works():
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--run-dir", str(FIXTURE), "--marker", "FAKE_REPAIR_TEST_FAILED",
                  "--output", d])
        assert r.returncode == 0, r.stderr
        assert "[WROTE]" in r.stderr
        # workspace + files exist
        ws = Path(d) / "repair_test_failed"
        assert (ws / "repair_proposal.json").exists()
        doc = json.loads((ws / "repair_proposal.json").read_text(encoding="utf-8"))
        assert doc["applied"] is False


def test_apply_is_rejected():
    r = _run(["--failure-report", str(REPORT), "--apply"])
    assert r.returncode != 0
    assert "REJECTED" in r.stderr
    assert "proposal only" in r.stderr.lower()
    # the script defines no apply implementation
    assert "def apply" not in SCRIPT_SRC


def test_output_redacted_no_secret():
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = FAKE_KEY
    with tempfile.TemporaryDirectory() as d:
        r = _run(["--run-dir", str(FIXTURE), "--marker", "FAKE_REPAIR_TEST_FAILED",
                  "--output", d], env=env)
        assert r.returncode == 0, r.stderr
        assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
        for f in (Path(d) / "repair_test_failed").iterdir():
            try:
                assert FAKE_KEY not in f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                pass


def test_script_does_not_modify_stable_or_run_shell():
    # No shell execution and no apply implementation anywhere in the script body.
    # (Protected-path names like promotion_policy/safety_gate appear only in the
    # docstring describing what the script does NOT do, so we check call patterns.)
    for needle in ("os.system", "subprocess.Popen", "subprocess.run",
                   "import subprocess", "shutil.copy", "def apply"):
        assert needle not in SCRIPT_SRC, needle


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
