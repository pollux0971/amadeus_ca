import json
import os
import tempfile
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.skills_runtime.simple_yaml import load_yaml
from src.orchestrator.orchestrator import Orchestrator

EVAL = ROOT / "evals" / "browser" / "open_localhost_keep_alive_smoke.yaml"


def _pid_alive(pid: int) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def test_browser_keep_alive_smoke_scores_1_and_no_lingering():
    task = load_yaml(EVAL)
    tmp = tempfile.mkdtemp(prefix="browser_e2e_runs_")
    orch = Orchestrator(task["id"], task["user_goal"], runs_dir=tmp)
    run_dir = orch.run_eval_task(task, eval_path=EVAL)
    score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))

    assert score["task_success"] is True
    assert score["score"] == 1.0
    crit = {r["criterion"]: r["passed"] for r in score["criteria_results"]}
    for name in ("server_started", "browser_page_loaded", "page_snapshot_created",
                 "result_json_created", "no_lingering_server_process"):
        assert crit[name] is True, (name, crit)

    # The kept-alive server was torn down by the orchestrator's finally cleanup.
    assert orch._server_sessions, "expected a keep-alive server session"
    time.sleep(0.2)
    for session in orch._server_sessions:
        assert not _pid_alive(session["pid"]), f"server {session['pid']} lingered after eval"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
