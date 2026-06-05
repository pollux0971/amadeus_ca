"""Candidate start_local_server v1 — real subprocess server lifecycle.

Replaces the placeholder with a runner that actually launches a local dev
server, detects its localhost URL from stdout/stderr within a timeout, writes
artifacts, and ALWAYS cleans up the process (success or failure) so nothing
lingers. v1 targets local Node/Vite-style fixtures.

Lifecycle note: v1 starts the server, detects the URL, records it, then
terminates the process group. It does NOT yet keep the server alive for a
downstream browser skill — that handoff is future work (see candidate_summary).
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
    """Resolve the dev-server command.

    Priority: explicit start_command > package.json scripts (dev, then start)
    > preferred_command (e.g. inspect_project's guess).
    """
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


def _write_artifacts(artifacts_dir: str | None, log_text: str, result: dict,
                     proc: "subprocess.Popen | None") -> dict:
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
    }
    (adir / "server.log").write_text(log_text, encoding="utf-8")
    process_info = {
        "pid": result.get("process_id"),
        "command": result.get("command"),
        "server_url": result.get("server_url"),
        "status": result.get("status"),
        "final_poll": (proc.poll() if proc is not None else None),
        "cleaned_up": True,
    }
    (adir / "process.json").write_text(
        json.dumps(process_info, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (adir / "result.json").write_text(
        json.dumps({**result, **refs}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return refs


def start_local_server(project_dir: str, preferred_command: str | None = None,
                       start_command: str | None = None, timeout_sec: int = 30,
                       artifacts_dir: str | None = None) -> dict:
    result: dict = {
        "status": "failed",
        "server_url": None,
        "process_id": None,
        "command": None,
        "log_ref": None,
        "result_ref": None,
        "process_ref": None,
        "failure_reason": None,
        "error": None,  # alias of failure_reason for back-compat
    }

    project_path = Path(project_dir)
    log_lines: list[str] = []
    proc: "subprocess.Popen | None" = None
    sandbox: Path | None = None
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
                start_new_session=True,  # own process group -> clean killpg
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
        _terminate(proc)
        if reader is not None:
            reader.join(timeout=2)
        result["error"] = result["failure_reason"]
        refs = _write_artifacts(artifacts_dir, "".join(log_lines), result, proc)
        result.update(refs)
        if sandbox is not None:
            shutil.rmtree(sandbox, ignore_errors=True)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--preferred-command", default=None)
    parser.add_argument("--start-command", default=None)
    parser.add_argument("--timeout-sec", type=int, default=30)
    parser.add_argument("--artifacts-dir", default=None)
    args = parser.parse_args()
    print(json.dumps(
        start_local_server(
            args.project_dir,
            preferred_command=args.preferred_command,
            start_command=args.start_command,
            timeout_sec=args.timeout_sec,
            artifacts_dir=args.artifacts_dir,
        ),
        ensure_ascii=False,
        indent=2,
    ))
