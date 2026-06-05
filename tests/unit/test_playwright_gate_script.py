import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SCRIPT = ROOT / "scripts" / "run_playwright_gate.py"
GATE_EVAL = ROOT / "evals" / "browser" / "open_localhost_playwright_required_smoke.yaml"


def _run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=str(ROOT))


def test_dry_run_does_not_execute_eval():
    proc = _run(["--dry-run"])
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.lower()
    assert "dry-run" in out
    assert "no browser launched" in out and "no eval executed" in out
    # run_eval prints "score=" on PASS/FAIL; dry-run must not have run it.
    assert "score=" not in proc.stdout


def test_missing_playwright_exits_2():
    # In an environment without the playwright package the gate must block with
    # exit code 2 (and never launch a browser or run the eval).
    if importlib.util.find_spec("playwright") is not None:
        return  # skip: playwright is installed here
    proc = _run([])
    assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
    assert "BLOCKED" in proc.stdout
    assert "Playwright is not installed" in proc.stdout
    assert "score=" not in proc.stdout  # eval was not run


def test_gate_script_does_not_install_anything():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "os.system" not in src
    # The only subprocess call targets run_eval.py — never an installer.
    for line in src.splitlines():
        if "subprocess" in line and "(" in line:
            assert "install" not in line, line
            assert "pip" not in line, line
    assert "run_eval" in src


def test_gate_eval_exists_and_requires_real_browser():
    assert GATE_EVAL.exists()
    text = GATE_EVAL.read_text(encoding="utf-8")
    assert "browser_mode: playwright" in text
    assert "require_real_browser: true" in text


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
