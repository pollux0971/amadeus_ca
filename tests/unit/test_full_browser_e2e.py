import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.orchestrator.orchestrator import EVIDENCE_RULES

FULL_EVAL = ROOT / "evals" / "browser" / "full_browser_vite_login_bug_e2e.yaml"
_HAS_PW = importlib.util.find_spec("playwright") is not None


# ---- evidence-rule unit tests (synthetic per-step outputs, aliased pre/post) ----

def _ev(name, o):
    return EVIDENCE_RULES[name](o)


def test_console_error_collected_uses_pre_patch_console():
    yes = {"console_pre": {"console_counts": {"error": 1, "fatal": 0}}, "console_post": {}}
    no = {"console_pre": {"console_counts": {"error": 0, "fatal": 0}}, "console_post": {}}
    assert _ev("console_error_collected", yes) is True
    assert _ev("console_error_collected", no) is False
    # legacy/vite path (non-aliased): key presence
    assert _ev("console_error_collected", {"read_browser_console": {"console_errors": []}}) is True


def test_patch_applied_and_tests_pass():
    o = {"patch_file_and_run_tests": {"patch_applied": True, "status": "passed", "test_passed": True}}
    assert _ev("patch_applied", o) is True
    assert _ev("tests_pass", o) is True
    bad = {"patch_file_and_run_tests": {"patch_applied": True, "status": "failed", "test_passed": False}}
    assert _ev("patch_applied", bad) is False
    assert _ev("tests_pass", bad) is False


def test_browser_reverify_passed_uses_post_open():
    ok = {"open_post": {"status": "loaded", "is_real_browser": True}}
    assert _ev("browser_reverify_passed", ok) is True
    assert _ev("browser_reverify_passed", {"open_post": {"status": "failed"}}) is False


def test_no_fatal_console_error_after_patch_uses_post_console():
    ok = {"console_post": {"status": "collected", "console_counts": {"fatal": 0}}}
    assert _ev("no_fatal_console_error_after_patch", ok) is True
    bad = {"console_post": {"status": "collected", "console_counts": {"fatal": 2}}}
    assert _ev("no_fatal_console_error_after_patch", bad) is False
    # a failed (unmeasured) post console must not pass
    assert _ev("no_fatal_console_error_after_patch", {"console_post": {"status": "failed"}}) is False


def test_real_browser_page_loaded_uses_pre_open():
    assert _ev("real_browser_page_loaded", {"open_pre": {"status": "loaded", "is_real_browser": True}}) is True


def test_no_lingering_checks_all_browser_steps():
    assert _ev("no_lingering_server_process",
               {"open_pre": {"browser_closed": True}, "console_post": {"browser_closed": True}}) is True
    assert _ev("no_lingering_server_process",
               {"open_pre": {"browser_closed": True}, "console_post": {"browser_closed": False}}) is False


def test_full_eval_has_aliased_pre_post_steps():
    text = FULL_EVAL.read_text(encoding="utf-8")
    assert "as: open_pre" in text and "as: console_pre" in text
    assert "as: open_post" in text and "as: console_post" in text


# ---- full e2e (Playwright only; skip cleanly without a real browser) ----

def test_full_browser_e2e_scores_1_when_playwright_present():
    if not _HAS_PW:
        return
    from src.skills_runtime.simple_yaml import load_yaml
    from src.orchestrator.orchestrator import Orchestrator
    task = load_yaml(FULL_EVAL)
    tmp = tempfile.mkdtemp(prefix="full_e2e_")
    orch = Orchestrator(task["id"], task["user_goal"], runs_dir=tmp)
    run_dir = orch.run_eval_task(task, eval_path=FULL_EVAL)
    score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))
    assert score["task_success"] is True and score["score"] == 1.0, score
    crit = {r["criterion"]: r["passed"] for r in score["criteria_results"]}
    for name in ("console_error_collected", "patch_applied", "tests_pass",
                 "browser_reverify_passed", "no_fatal_console_error_after_patch",
                 "no_lingering_server_process"):
        assert crit[name] is True, (name, crit)
    # server torn down by the orchestrator finally
    for sess in orch._server_sessions:
        try:
            os.kill(sess["pid"], 0)
            alive = True
        except (ProcessLookupError, OSError):
            alive = False
        assert not alive, "server lingered after full e2e"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
