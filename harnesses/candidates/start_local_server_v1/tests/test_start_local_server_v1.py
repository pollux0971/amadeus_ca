import importlib.util
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
_spec = importlib.util.spec_from_file_location("candidate_start_server_under_test", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

FIXTURE = CAND / "fixtures" / "tiny_node_server"
SERVER_JS = FIXTURE / "server.js"


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


def test_detect_vite_dev_command():
    # package.json with a "dev" script resolves to `npm run dev`.
    assert mod.resolve_start_command(FIXTURE) == "npm run dev"


def test_detect_start_command_fallback_and_explicit_override():
    d = Path(tempfile.mkdtemp())
    try:
        (d / "package.json").write_text('{"scripts": {"start": "node server.js"}}', encoding="utf-8")
        assert mod.resolve_start_command(d) == "npm start"
        # explicit start_command always wins
        assert mod.resolve_start_command(FIXTURE, start_command="node server.js") == "node server.js"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_unsafe_command_blocked():
    d = Path(tempfile.mkdtemp())
    try:
        r = mod.start_local_server(str(FIXTURE), start_command="sudo node server.js",
                                   timeout_sec=5, artifacts_dir=str(d / "a"))
        assert r["status"] == "failed"
        assert "command_blocked" in (r["failure_reason"] or "")
        assert r["server_url"] is None
        assert r["process_id"] is None  # never launched
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_localhost_url_detected_and_artifacts():
    d = Path(tempfile.mkdtemp())
    try:
        # Auto-detect path: package.json dev -> npm run dev -> node server.js.
        r = mod.start_local_server(str(FIXTURE), timeout_sec=25, artifacts_dir=str(d / "a"))
        assert r["status"] == "started", r
        assert r["server_url"] and "127.0.0.1" in r["server_url"], r
        assert (d / "a" / "server.log").exists()
        assert (d / "a" / "result.json").exists()
        assert (d / "a" / "process.json").exists()
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_process_cleanup_no_lingering():
    d = Path(tempfile.mkdtemp())
    try:
        r = mod.start_local_server(str(FIXTURE), start_command="node server.js",
                                   timeout_sec=25, artifacts_dir=str(d / "a"))
        assert r["status"] == "started", r
        pid = r["process_id"]
        # Give the OS a moment, then confirm the process group is gone.
        time.sleep(0.2)
        assert not _pid_alive(pid), f"server process {pid} lingered"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_timeout_failure_reason_and_cleanup():
    d = Path(tempfile.mkdtemp())
    try:
        # A command that never prints a URL must time out and be cleaned up.
        r = mod.start_local_server(str(FIXTURE), start_command="sleep 5",
                                   timeout_sec=1, artifacts_dir=str(d / "a"))
        assert r["status"] == "failed"
        assert "timeout_no_url" in (r["failure_reason"] or ""), r
        pid = r["process_id"]
        time.sleep(0.2)
        assert not _pid_alive(pid), f"timed-out process {pid} lingered"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_fixture_not_mutated():
    before_js = SERVER_JS.read_text(encoding="utf-8")
    before_pkg = (FIXTURE / "package.json").read_text(encoding="utf-8")
    d = Path(tempfile.mkdtemp())
    try:
        mod.start_local_server(str(FIXTURE), start_command="node server.js",
                               timeout_sec=25, artifacts_dir=str(d / "a"))
    finally:
        shutil.rmtree(d, ignore_errors=True)
    assert SERVER_JS.read_text(encoding="utf-8") == before_js
    assert (FIXTURE / "package.json").read_text(encoding="utf-8") == before_pkg


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
