import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SCRIPT = ROOT / "scripts" / "run_full_browser_gate.py"
FULL_EVAL = ROOT / "evals" / "browser" / "full_browser_vite_login_bug_e2e.yaml"

_spec = importlib.util.spec_from_file_location("run_full_browser_gate_under_test", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=str(ROOT))


def test_dry_run_does_not_execute_eval():
    proc = _run(["--dry-run"])
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.lower()
    assert "dry-run" in out
    assert "no browser launched" in out and "no eval executed" in out
    assert "score=" not in proc.stdout  # the eval was not run


def test_missing_prereqs_block_with_exit_2():
    # In this environment Playwright is absent AND the read_browser_console
    # candidate does not exist, so the gate must block with exit code 2.
    proc = _run([])
    assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
    out = proc.stdout
    assert "BLOCKED" in out
    assert "playwright_python_package" in out
    assert "read_browser_console_candidate_exists" in out
    assert "score=" not in out  # eval was not run


def test_read_browser_console_candidate_prereq_is_unmet():
    # Directly verify the console-candidate prerequisite is unmet (it is blocked).
    assert mod.console_candidate_exists(ROOT) is False
    prereqs = {p["name"]: p["met"] for p in mod.evaluate_prerequisites(ROOT)}
    assert prereqs["read_browser_console_candidate_exists"] is False
    assert prereqs["playwright_python_package"] is False


def test_gate_script_does_not_install_anything():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "os.system" not in src
    for line in src.splitlines():
        if "subprocess" in line and "(" in line:
            assert "install" not in line, line
            assert "pip" not in line, line
    assert "run_eval" in src


def test_full_browser_eval_exists_and_is_blocked_draft():
    assert FULL_EVAL.exists()
    text = FULL_EVAL.read_text(encoding="utf-8")
    assert "browser_mode: playwright" in text
    assert "require_real_browser: true" in text
    assert "blocked_until" in text


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
