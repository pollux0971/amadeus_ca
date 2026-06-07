import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EVAL = ROOT / "evals" / "dashboard" / "ui_dashboard_readonly_smoke.yaml"
RUNNER = ROOT / "scripts" / "run_dashboard_smoke.py"
REPORT = ROOT / "reports" / "story_ui_dashboard_smoke_v0" / "README.md"

REQUIRED_CRITERIA = [
    "snapshot_generated", "dashboard_validated", "page_loaded", "title_visible",
    "heading_visible", "latest_checkpoint_visible", "phase_status_visible",
    "eval_status_visible", "snapshot_visible", "no_button", "no_form", "no_onclick",
    "no_post_action", "no_external_request", "no_secret_in_body", "no_action_trigger",
    "browser_teardown", "server_teardown", "no_lingering_process",
]


def test_smoke_files_exist():
    assert EVAL.exists()
    assert RUNNER.exists()
    assert REPORT.exists()


def test_eval_declares_readonly_and_teardown_criteria():
    from src.skills_runtime.simple_yaml import load_yaml
    task = load_yaml(EVAL)
    crit = task.get("success_criteria") or []
    for c in REQUIRED_CRITERIA:
        assert c in crit, f"smoke eval missing criterion {c!r}"
    assert task.get("category") == "dashboard"


def test_runner_is_shell_free_and_in_process():
    src = RUNNER.read_text(encoding="utf-8")
    assert "shell=True" not in src
    assert "os.system" not in src
    assert "subprocess" not in src  # uses an in-process http.server, not a shell
    assert "http.server" in src
    assert "--dry-run" in src
    # serves only localhost, asserts external requests are rejected
    assert "127.0.0.1" in src and "no_external_request" in src


def test_dry_run_runs_nothing_and_exits_zero():
    r = subprocess.run([sys.executable, str(RUNNER), "--dry-run"],
                       capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0, r.stderr
    out = r.stdout.lower()
    assert "dry-run" in out
    assert "no browser launched" in out
    assert "[pass]" not in out  # nothing actually executed


def test_validator_covers_smoke():
    spec = importlib.util.spec_from_file_location(
        "validate_dashboard", ROOT / "scripts" / "validate_dashboard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "evals/dashboard/ui_dashboard_readonly_smoke.yaml" in mod.REQUIRED_FILES
    assert "scripts/run_dashboard_smoke.py" in mod.REQUIRED_FILES
    assert mod.check(ROOT) == [], mod.check(ROOT)


def test_real_browser_smoke_when_playwright_available():
    # Real-browser run only when Playwright is present (e.g. the project .venv).
    # Under the system interpreter (no Playwright) this is skipped so run_unit_tests
    # stays green; the gate itself is exercised via scripts/run_dashboard_smoke.py.
    if importlib.util.find_spec("playwright") is None:
        return  # skip: no Playwright runtime here
    r = subprocess.run([sys.executable, str(RUNNER)], capture_output=True, text=True,
                       cwd=str(ROOT))
    assert r.returncode == 0, r.stderr
    assert "score=1.0" in r.stdout


def test_no_secret_in_smoke_artifacts():
    from src.llm.redaction import redact_text
    for f in (EVAL, RUNNER, REPORT):
        text = f.read_text(encoding="utf-8")
        assert redact_text(text) == text, f"secret-like content in {f}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
