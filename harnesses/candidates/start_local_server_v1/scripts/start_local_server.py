"""Candidate start_local_server v1.1 — real subprocess server lifecycle with an
optional keep-alive + teardown handoff.

- keep_alive=False (default): unchanged v1 behavior — start, detect the localhost
  URL, write artifacts, and ALWAYS terminate the process group in `finally`.
- keep_alive=True: start, detect the URL, write artifacts plus a
  `server_session.json`, and leave the process + sandbox alive so a later step
  can use server_url. The caller (or the orchestrator) tears it down via
  `teardown(session)`.

v1.1 targets local Node/Vite-style fixtures. It executes shell commands, so
promotion needs human review (promotion_policy.md).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

# Bootstrap the repo root so ``src...`` imports resolve when run standalone.
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agents.safety_gate.command_policy import check_command

_URL_RE = re.compile(r"https?://(?:localhost|127\.0\.0\.1):\d+")


class ServerError(Exception):
    """Raised when the server cannot be started or no URL is detected."""


def detect_localhost_url(text: str) -> str | None:
    match = _URL_RE.search(text)
    return match.group(0) if match else None


def resolve_start_command(workdir: Path, preferred_command: str | None = None,
                          start_command: str | None = None) -> str | None:
    """Priority: explicit start_command > package.json dev/start > preferred."""
    if start_command:
        return start_command
    pkg = workdir / "package.json"
    if pkg.exists():
        try:
            scripts = (json.loads(pkg.read_text(encoding="utf-8")).get("scripts") or {})
        except json.JSONDecodeError:
            scripts = {}
        if "dev" in scripts:
            return "npm run dev"
        if "start" in scripts:
            return "npm start"
    return preferred_command or None


def _is_within(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _pgid_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _safe_pgid(proc: "subprocess.Popen") -> int:
    try:
        return os.getpgid(proc.pid)
    except (ProcessLookupError, PermissionError):
        return proc.pid


def _terminate(proc: "subprocess.Popen | None") -> None:
    """Kill the whole process group; never raise. Always reaps the child."""
    if proc is None:
        return
    if proc.poll() is None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(os.getpgid(proc.pid), sig)
            except (ProcessLookupError, PermissionError):
                break
            try:
                proc.wait(timeout=5)
                break
            except subprocess.TimeoutExpired:
                continue
    try:
        proc.wait(timeout=5)
    except (subprocess.TimeoutExpired, Exception):  # noqa: BLE001
        pass


def teardown(session) -> dict:
    """Tear down a kept-alive server from its session (dict or path to
    server_session.json). Kills the process group and removes the sandbox.

    Idempotent: calling it again after the server is gone returns cleanly and
    never raises.
    """
    if isinstance(session, (str, Path)):
        path = Path(session)
        session = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    session = session or {}

    pgid = session.get("pgid")
    pid = session.get("pid")
    workdir = session.get("workdir")
    killed = False

    if pgid is not None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(pgid, sig)
                killed = True
            except (ProcessLookupError, PermissionError):
                break
            time.sleep(0.1)
            if not _pgid_alive(pgid):
                break
    elif pid is not None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.kill(pid, sig)
                killed = True
            except (ProcessLookupError, PermissionError):
                break
            time.sleep(0.1)

    if workdir:
        # workdir is <sandbox>/<fixture>; remove the whole temp sandbox.
        try:
            shutil.rmtree(Path(workdir).parent, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass

    return {"server_id": session.get("server_id"), "torn_down": True, "killed": killed}


def _write_artifacts(artifacts_dir: str | None, log_text: str, result: dict,
                     proc: "subprocess.Popen | None", session: dict | None) -> dict:
    if artifacts_dir:
        adir = Path(artifacts_dir)
        prefix = "artifacts"
    else:
        adir = Path(tempfile.mkdtemp(prefix="server_artifacts_"))
        prefix = str(adir)
    adir.mkdir(parents=True, exist_ok=True)

    refs = {
        "log_ref": f"{prefix}/server.log",
        "result_ref": f"{prefix}/result.json",
        "process_ref": f"{prefix}/process.json",
        "server_session_ref": None,
    }
    (adir / "server.log").write_text(log_text, encoding="utf-8")
    process_info = {
        "pid": result.get("process_id"),
        "command": result.get("command"),
        "server_url": result.get("server_url"),
        "status": result.get("status"),
        "final_poll": (proc.poll() if proc is not None else None),
        "cleaned_up": session is None,  # kept-alive sessions are not cleaned up here
    }
    (adir / "process.json").write_text(
        json.dumps(process_info, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if session is not None:
        refs["server_session_ref"] = f"{prefix}/server_session.json"
        session["log_ref"] = refs["log_ref"]
        (adir / "server_session.json").write_text(
            json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    (adir / "result.json").write_text(
        json.dumps({**result, **refs}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return refs


def start_local_server(project_dir: str, preferred_command: str | None = None,
                       start_command: str | None = None, timeout_sec: int = 30,
                       artifacts_dir: str | None = None, keep_alive: bool = False,
                       lease_ttl_sec: int = 300,
                       teardown_policy: str = "process_group") -> dict:
    result: dict = {
        "status": "failed",
        "server_url": None,
        "process_id": None,
        "command": None,
        "keep_alive": bool(keep_alive),
        "server_session": None,
        "log_ref": None,
        "result_ref": None,
        "process_ref": None,
        "server_session_ref": None,
        "failure_reason": None,
        "error": None,  # alias of failure_reason for back-compat
    }

    project_path = Path(project_dir)
    log_lines: list[str] = []
    proc: "subprocess.Popen | None" = None
    sandbox: Path | None = None
    work: Path | None = None
    reader: threading.Thread | None = None

    try:
        if not project_path.exists():
            raise ServerError("project_dir_not_found")

        sandbox = Path(tempfile.mkdtemp(prefix="server_ws_"))
        work = sandbox / project_path.name
        shutil.copytree(project_path, work)

        cmd = resolve_start_command(work, preferred_command, start_command)
        result["command"] = cmd
        if not cmd:
            raise ServerError("no_start_command")

        allowed, reason = check_command(cmd)
        if not allowed:
            raise ServerError(f"command_blocked: {reason}")

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(work),
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                bufsize=1,
            )
        except Exception as exc:  # noqa: BLE001
            raise ServerError(f"spawn_error: {exc}")
        result["process_id"] = proc.pid

        found = threading.Event()

        def _read() -> None:
            try:
                for line in proc.stdout:  # type: ignore[union-attr]
                    log_lines.append(line)
                    if not found.is_set():
                        url = detect_localhost_url(line)
                        if url:
                            result["server_url"] = url
                            found.set()
            except Exception:  # noqa: BLE001
                pass

        reader = threading.Thread(target=_read, daemon=True)
        reader.start()

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if found.is_set():
                break
            if proc.poll() is not None:
                break
            time.sleep(0.05)

        if found.is_set():
            result["status"] = "started"
        elif proc.poll() is not None:
            raise ServerError(f"server_exited_early: returncode={proc.returncode}")
        else:
            raise ServerError("timeout_no_url")

    except ServerError as exc:
        result["failure_reason"] = str(exc)
        result["status"] = "failed"
    finally:
        keep = bool(keep_alive) and result["status"] == "started" and proc is not None
        if keep:
            # Hand off a live server: build the session, write artifacts, and
            # leave the process + sandbox running. Teardown is the caller's job.
            session = {
                "server_id": uuid.uuid4().hex,
                "server_url": result["server_url"],
                "pid": proc.pid,
                "pgid": _safe_pgid(proc),
                "workdir": str(work) if work is not None else None,
                "log_ref": None,  # filled by _write_artifacts
                "lease_ttl_sec": int(lease_ttl_sec),
                "teardown_policy": teardown_policy,
            }
            result["server_session"] = session
            refs = _write_artifacts(artifacts_dir, "".join(log_lines), result, proc, session)
            result.update(refs)
            # NOTE: do not terminate, do not join the reader, do not rmtree.
        else:
            _terminate(proc)
            if reader is not None:
                reader.join(timeout=2)
            refs = _write_artifacts(artifacts_dir, "".join(log_lines), result, proc, None)
            result.update(refs)
            if sandbox is not None:
                shutil.rmtree(sandbox, ignore_errors=True)
        result["error"] = result["failure_reason"]

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--preferred-command", default=None)
    parser.add_argument("--start-command", default=None)
    parser.add_argument("--timeout-sec", type=int, default=30)
    parser.add_argument("--artifacts-dir", default=None)
    parser.add_argument("--keep-alive", action="store_true")
    parser.add_argument("--lease-ttl-sec", type=int, default=300)
    args = parser.parse_args()
    print(json.dumps(
        start_local_server(
            args.project_dir,
            preferred_command=args.preferred_command,
            start_command=args.start_command,
            timeout_sec=args.timeout_sec,
            artifacts_dir=args.artifacts_dir,
            keep_alive=args.keep_alive,
            lease_ttl_sec=args.lease_ttl_sec,
        ),
        ensure_ascii=False,
        indent=2,
    ))
