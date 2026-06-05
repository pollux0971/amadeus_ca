import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

CAND = Path(__file__).resolve().parents[1]
SCRIPT = CAND / "scripts" / "start_local_server.py"
_spec = importlib.util.spec_from_file_location("candidate_reaper_under_test", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

FIXTURE = CAND / "fixtures" / "tiny_node_server"


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


def _start(sd: Path, lease_ttl_sec: int):
    return mod.start_local_server(
        str(FIXTURE), start_command="node server.js", timeout_sec=20,
        keep_alive=True, lease_ttl_sec=lease_ttl_sec, sessions_dir=str(sd),
    )["server_session"]


def test_expired_session_is_reaped():
    sd = Path(tempfile.mkdtemp())
    try:
        s = _start(sd, lease_ttl_sec=1)
        assert _pid_alive(s["pid"])
        rep = mod.reap_sessions(sessions_dir=str(sd), now=s["started_at"] + 10)
        time.sleep(0.2)
        assert len(rep["reaped"]) == 1 and rep["kept"] == [], rep
        assert not _pid_alive(s["pid"]), "expired server should be killed"
        assert not Path(s["session_file"]).exists(), "registry file should be removed"
        assert not Path(s["workdir"]).exists(), "sandbox should be removed"
    finally:
        shutil.rmtree(sd, ignore_errors=True)


def test_non_expired_session_is_kept():
    sd = Path(tempfile.mkdtemp())
    s = None
    try:
        s = _start(sd, lease_ttl_sec=3600)
        rep = mod.reap_sessions(sessions_dir=str(sd), now=s["started_at"] + 5)
        assert rep["reaped"] == [] and len(rep["kept"]) == 1, rep
        assert _pid_alive(s["pid"]), "non-expired server must keep running"
        assert Path(s["session_file"]).exists()
    finally:
        if s:
            mod.teardown(s)
        shutil.rmtree(sd, ignore_errors=True)


def test_missing_process_handled_idempotently():
    sd = Path(tempfile.mkdtemp())
    try:
        s = _start(sd, lease_ttl_sec=1)
        mod.teardown(s)  # kill now; registry file remains, process is gone
        time.sleep(0.2)
        assert not _pid_alive(s["pid"])
        # Reaping an already-dead session must not raise.
        rep = mod.reap_sessions(sessions_dir=str(sd), now=s["started_at"] + 10)
        assert len(rep["reaped"]) == 1, rep
        assert rep["errors"] == []
        assert not Path(s["session_file"]).exists()
    finally:
        shutil.rmtree(sd, ignore_errors=True)


def test_corrupt_session_reported_not_crash():
    sd = Path(tempfile.mkdtemp())
    try:
        (sd / "corrupt.json").write_text("{not valid json", encoding="utf-8")
        (sd / "incomplete.json").write_text(json.dumps({"server_id": "x"}), encoding="utf-8")
        rep = mod.reap_sessions(sessions_dir=str(sd), now=time.time())
        reasons = " ".join(e["failure_reason"] for e in rep["errors"])
        assert "corrupt_session_json" in reasons, rep
        assert "missing_started_at_or_lease_ttl_sec" in reasons, rep
        assert rep["reaped"] == []  # nothing killed/deleted on errors
    finally:
        shutil.rmtree(sd, ignore_errors=True)


def test_dry_run_does_not_kill_or_delete():
    sd = Path(tempfile.mkdtemp())
    s = None
    try:
        s = _start(sd, lease_ttl_sec=1)
        rep = mod.reap_sessions(sessions_dir=str(sd), now=s["started_at"] + 100, dry_run=True)
        time.sleep(0.2)
        assert len(rep["reaped"]) == 1 and rep["reaped"][0].get("dry_run") is True, rep
        assert _pid_alive(s["pid"]), "dry_run must not kill the server"
        assert Path(s["session_file"]).exists(), "dry_run must not delete the registry file"
        assert Path(s["workdir"]).exists(), "dry_run must not delete the sandbox"
    finally:
        if s:
            mod.teardown(s)
        shutil.rmtree(sd, ignore_errors=True)


def test_reaper_writes_report_and_skips_its_own_report():
    sd = Path(tempfile.mkdtemp())
    try:
        (sd / "incomplete.json").write_text(json.dumps({"server_id": "x"}), encoding="utf-8")
        report_path = sd / "reaper_report.json"
        rep = mod.reap_sessions(sessions_dir=str(sd), now=time.time(), report_path=str(report_path))
        assert report_path.exists()
        on_disk = json.loads(report_path.read_text(encoding="utf-8"))
        assert on_disk["scanned"] == 1  # the report file itself is not scanned
    finally:
        shutil.rmtree(sd, ignore_errors=True)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
