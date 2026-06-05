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

EVAL = ROOT / "evals" / "server" / "keep_alive_smoke.yaml"


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


def test_keep_alive_session_is_torn_down_after_eval():
    task = load_yaml(EVAL)
    tmp = tempfile.mkdtemp(prefix="keepalive_runs_")
    orch = Orchestrator(task["id"], task["user_goal"], runs_dir=tmp)
    run_dir = orch.run_eval_task(task, eval_path=EVAL)
    score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))

    # The keep-alive server made dev_server_started true.
    assert score["task_success"] is True
    crit = {r["criterion"]: r["passed"] for r in score["criteria_results"]}
    assert crit["dev_server_started"] is True

    # A kept-alive session was created during the run...
    assert orch._server_sessions, "expected a keep-alive server session"
    # ...and the orchestrator's finally cleanup tore it down (no lingering).
    time.sleep(0.2)
    for session in orch._server_sessions:
        assert not _pid_alive(session["pid"]), f"server {session['pid']} lingered after eval"
        # sandbox removed too
        assert not Path(session["workdir"]).exists()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
