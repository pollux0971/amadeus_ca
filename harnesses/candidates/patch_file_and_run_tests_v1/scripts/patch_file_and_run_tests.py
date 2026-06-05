"""Candidate patch runner v1 — vite_login_bug demo only.

Applies the known minimal fix to ``src/App.jsx`` on an isolated sandbox copy
of the fixture (the committed fixture is never mutated), runs the eval's
test command through the Safety Gate, and writes patch.diff / test.log /
result.json artifacts.

This deliberately targets a single demo. It is a ``dev`` candidate and must
not be promoted to a general patch tool without human review (it runs shell
commands — see specs/harness/promotion_policy.md).
"""
from __future__ import annotations

import difflib
import json
import shutil
import sys
import tempfile
from pathlib import Path

# Bootstrap the repo root so ``src...`` imports resolve when this script is
# run standalone (the harness executor and unit runner add it too).
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agents.cli_agent.command_runner import run_command

TARGET_REL = "src/App.jsx"
EXAMPLE_REL = "src/App.fixed.example.jsx"

# Fallback line-level fix if the worked example file is absent.
_FALLBACK_REPLACEMENTS = [
    ("const user = undefined;", 'const user = { token: "" };'),
    ("const token = user.token;", "const token = user?.token ?? \"\";"),
    ("  // Intentional runtime bug:\n", ""),
]


def _is_within(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _build_fixed_content(project_path: Path) -> tuple[str, str]:
    original = (project_path / TARGET_REL).read_text(encoding="utf-8")
    example = project_path / EXAMPLE_REL
    if example.exists():
        return original, example.read_text(encoding="utf-8")
    fixed = original
    for old, new in _FALLBACK_REPLACEMENTS:
        fixed = fixed.replace(old, new)
    return original, fixed


def _write_artifacts(artifacts_dir: str | None, diff_text: str, test_log: str,
                     result: dict) -> dict:
    if artifacts_dir:
        adir = Path(artifacts_dir)
        ref_prefix = "artifacts"
    else:
        adir = Path(tempfile.mkdtemp(prefix="patch_artifacts_"))
        ref_prefix = str(adir)
    adir.mkdir(parents=True, exist_ok=True)

    refs = {
        "diff_ref": f"{ref_prefix}/patch.diff",
        "test_output_ref": f"{ref_prefix}/test.log",
        "result_ref": f"{ref_prefix}/result.json",
    }
    (adir / "patch.diff").write_text(diff_text, encoding="utf-8")
    (adir / "test.log").write_text(test_log, encoding="utf-8")
    (adir / "result.json").write_text(
        json.dumps({**result, **refs}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return refs


def patch_and_run(project_dir: str, test_command: str, patch: str = "",
                  artifacts_dir: str | None = None, timeout_sec: int = 60) -> dict:
    result: dict = {
        "patch_applied": False,
        "test_passed": False,
        "status": "failed",
        "target_file": TARGET_REL,
        "test_command": test_command,
        "returncode": None,
        "diff_ref": None,
        "test_output_ref": None,
        "result_ref": None,
        "error": None,
    }

    project_path = Path(project_dir)
    if not project_path.exists():
        result["error"] = "project_dir_not_found"
        return result
    if not (project_path / TARGET_REL).exists():
        result["error"] = "target_file_not_found"
        return result

    original, fixed = _build_fixed_content(project_path)
    diff_text = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f"a/{TARGET_REL}",
            tofile=f"b/{TARGET_REL}",
        )
    )

    # Work on an isolated copy; never mutate the committed fixture.
    sandbox = Path(tempfile.mkdtemp(prefix="patch_ws_"))
    test_log = ""
    try:
        work = sandbox / project_path.name
        shutil.copytree(project_path, work)
        work_target = work / TARGET_REL
        if not _is_within(work, work_target):
            result["error"] = "unsafe_path"
            return result

        work_target.write_text(fixed, encoding="utf-8")
        result["patch_applied"] = work_target.read_text(encoding="utf-8") == fixed

        # Run the test command through the Safety Gate (run_command enforces it).
        cmd = run_command(test_command, cwd=work, timeout_sec=timeout_sec)
        test_log = (
            f"$ {test_command}\n"
            f"[allowed={cmd.allowed}] returncode={cmd.returncode}\n"
            f"--- stdout ---\n{cmd.stdout}\n"
            f"--- stderr ---\n{cmd.stderr}\n"
        )
        result["returncode"] = cmd.returncode
        if not cmd.allowed:
            result["error"] = f"command_blocked: {cmd.block_reason}"
        result["test_passed"] = bool(cmd.allowed and cmd.returncode == 0)
        result["status"] = "passed" if (result["patch_applied"] and result["test_passed"]) else "failed"
    finally:
        refs = _write_artifacts(artifacts_dir, diff_text, test_log, result)
        result.update(refs)
        shutil.rmtree(sandbox, ignore_errors=True)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--patch", default="")
    parser.add_argument("--test-command", required=True)
    parser.add_argument("--artifacts-dir", default=None)
    parser.add_argument("--timeout-sec", type=int, default=60)
    args = parser.parse_args()
    print(json.dumps(
        patch_and_run(
            args.project_dir,
            test_command=args.test_command,
            patch=args.patch,
            artifacts_dir=args.artifacts_dir,
            timeout_sec=args.timeout_sec,
        ),
        ensure_ascii=False,
        indent=2,
    ))
