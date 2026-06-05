from __future__ import annotations

import subprocess
from pathlib import Path
from dataclasses import dataclass

from src.agents.safety_gate.command_policy import check_command


@dataclass
class CommandResult:
    command: str
    allowed: bool
    returncode: int | None
    stdout: str
    stderr: str
    block_reason: str | None = None


def run_command(command: str, cwd: str | Path = ".", timeout_sec: int = 30) -> CommandResult:
    allowed, reason = check_command(command)
    if not allowed:
        return CommandResult(command=command, allowed=False, returncode=None, stdout="", stderr="", block_reason=reason)

    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
        )
        return CommandResult(command=command, allowed=True, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(command=command, allowed=True, returncode=124, stdout=exc.stdout or "", stderr=exc.stderr or "command timeout")
