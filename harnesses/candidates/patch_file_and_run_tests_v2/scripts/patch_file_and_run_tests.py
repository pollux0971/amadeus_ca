"""Candidate patch runner v2 — reusable, plan-driven patch runner.

Unlike v1 (which hard-coded the vite App.jsx fix), v2 has no fixture-specific
code. It applies a declarative ``patch_plan`` to an isolated sandbox copy of a
fixture, emits a real unified diff, runs the plan's test command through the
Safety Gate, and writes patch.diff / test.log / result.json.

A patch_plan is a dict:

    {
      "description": "...",            # optional
      "test_command": "npm test",      # optional (arg overrides this)
      "patches": [
        {"type": "replace_text", "file": "src/App.jsx",
         "find": "...", "replace": "...", "count": 1},   # count optional
        {"type": "unified_diff", "file": "calc.py", "diff": "<unified diff>"},
      ],
    }

When no explicit plan is passed, the runner loads ``<plans_dir>/<fixture>.yaml``
where ``<fixture>`` is the basename of ``project_dir`` and ``plans_dir`` defaults
to this candidate's ``plans/`` directory. That is what proves it is not
hard-coded: a new fixture only needs a new declarative plan, not new code.
"""
from __future__ import annotations

import difflib
import json
import shutil
import sys
import tempfile
from pathlib import Path

# Bootstrap the repo root so ``src...`` imports resolve when run standalone.
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agents.cli_agent.command_runner import run_command
from src.skills_runtime.simple_yaml import load_yaml

_DEFAULT_PLANS_DIR = Path(__file__).resolve().parents[1] / "plans"


# --------------------------------------------------------------------------- #
# Patch plan engine
# --------------------------------------------------------------------------- #

class PatchError(Exception):
    """Raised when a patch cannot be applied cleanly."""


def apply_unified_diff(text: str, diff: str) -> str:
    """Apply a standard unified diff to ``text`` and return the new text.

    Raises PatchError on any context/removal mismatch. Operates line-wise;
    a trailing newline in the source is preserved.
    """
    src = text.split("\n")
    out: list[str] = []
    src_pos = 0

    diff_lines = diff.split("\n")
    i = 0
    n = len(diff_lines)
    while i < n:
        line = diff_lines[i]
        if line.startswith("--- ") or line.startswith("+++ "):
            i += 1
            continue
        if line.startswith("@@"):
            old_start = _parse_hunk_old_start(line)
            old_idx = old_start - 1  # 0-based
            if old_idx < src_pos:
                raise PatchError(f"overlapping hunk at line {old_start}")
            out.extend(src[src_pos:old_idx])
            src_pos = old_idx
            i += 1
            # consume hunk body until next header/EOF
            while i < n and not diff_lines[i].startswith("@@"):
                body = diff_lines[i]
                i += 1
                if body and (body.startswith("--- ") or body.startswith("+++ ")):
                    continue
                if body.startswith("\\"):  # "\ No newline at end of file"
                    continue
                tag = body[0] if body else " "
                content = body[1:] if body else ""
                if tag == " ":
                    if src_pos >= len(src) or src[src_pos] != content:
                        raise PatchError(f"context mismatch at source line {src_pos + 1}")
                    out.append(src[src_pos])
                    src_pos += 1
                elif tag == "-":
                    if src_pos >= len(src) or src[src_pos] != content:
                        raise PatchError(f"removal mismatch at source line {src_pos + 1}")
                    src_pos += 1
                elif tag == "+":
                    out.append(content)
                else:
                    raise PatchError(f"unrecognized diff line: {body!r}")
            continue
        # ignore anything outside a hunk
        i += 1

    out.extend(src[src_pos:])
    return "\n".join(out)


def _parse_hunk_old_start(header: str) -> int:
    # @@ -l,s +l,s @@
    try:
        minus = header.split("-", 1)[1]
        nums = minus.split(" ", 1)[0]
        return int(nums.split(",", 1)[0])
    except (IndexError, ValueError) as exc:
        raise PatchError(f"bad hunk header: {header!r}") from exc


def _apply_one(workdir: Path, patch: dict) -> str:
    """Apply a single patch entry in-place; return the modified file's rel path."""
    ptype = patch.get("type")
    rel = patch.get("file")
    if not rel:
        raise PatchError("patch entry missing 'file'")
    target = workdir / rel
    if not _is_within(workdir, target):
        raise PatchError(f"unsafe_path: {rel}")
    if not target.exists():
        raise PatchError(f"target_file_not_found: {rel}")

    original = target.read_text(encoding="utf-8")
    if ptype == "replace_text":
        find = patch.get("find", "")
        replace = patch.get("replace", "")
        if find == "" or find not in original:
            raise PatchError(f"target_text_not_found in {rel}")
        count = patch.get("count")
        new = original.replace(find, replace, count) if count else original.replace(find, replace)
    elif ptype == "unified_diff":
        diff = patch.get("diff", "")
        if not diff.strip():
            raise PatchError(f"empty unified_diff for {rel}")
        new = apply_unified_diff(original, diff)
    else:
        raise PatchError(f"unknown_patch_type: {ptype!r}")

    target.write_text(new, encoding="utf-8")
    return rel


def _is_within(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# Plan resolution + artifacts
# --------------------------------------------------------------------------- #

def _resolve_plan(project_dir: Path, plan: dict | None, plans_dir: str | Path | None) -> dict:
    if plan is not None:
        return plan
    base = Path(plans_dir) if plans_dir else _DEFAULT_PLANS_DIR
    plan_path = base / f"{project_dir.name}.yaml"
    if not plan_path.exists():
        raise PatchError(f"plan_not_found: {plan_path}")
    loaded = load_yaml(plan_path) or {}
    if not loaded.get("patches"):
        raise PatchError(f"plan_has_no_patches: {plan_path}")
    return loaded


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


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def patch_and_run(project_dir: str, test_command: str | None = None, patch: str = "",
                  artifacts_dir: str | None = None, plan: dict | None = None,
                  plans_dir: str | None = None, timeout_sec: int = 60) -> dict:
    result: dict = {
        "patch_applied": False,
        "test_passed": False,
        "status": "failed",
        "failure_reason": None,
        "target_files": [],
        "test_command": test_command,
        "returncode": None,
        "diff_ref": None,
        "test_output_ref": None,
        "result_ref": None,
        "error": None,  # kept as an alias of failure_reason for back-compat
    }

    project_path = Path(project_dir)
    diff_text = ""
    test_log = ""
    sandbox: Path | None = None

    try:
        if not project_path.exists():
            raise PatchError("project_dir_not_found")

        plan_obj = _resolve_plan(project_path, plan, plans_dir)
        patches = plan_obj.get("patches") or []
        effective_test_command = test_command or plan_obj.get("test_command")
        result["test_command"] = effective_test_command

        # Work on an isolated copy; never mutate the source fixture.
        sandbox = Path(tempfile.mkdtemp(prefix="patch_ws_"))
        work = sandbox / project_path.name
        shutil.copytree(project_path, work)

        # Snapshot originals so patch.diff reflects every touched file.
        originals: dict[str, str] = {}
        touched: list[str] = []
        for entry in patches:
            rel = entry.get("file")
            if rel and rel not in originals:
                f = work / rel
                originals[rel] = f.read_text(encoding="utf-8") if f.exists() else ""
            applied_rel = _apply_one(work, entry)
            if applied_rel not in touched:
                touched.append(applied_rel)

        result["patch_applied"] = bool(touched)
        result["target_files"] = touched

        diff_text = _aggregate_diff(work, originals)

        if not effective_test_command:
            raise PatchError("no_test_command")

        cmd = run_command(effective_test_command, cwd=work, timeout_sec=timeout_sec)
        test_log = (
            f"$ {effective_test_command}\n"
            f"[allowed={cmd.allowed}] returncode={cmd.returncode}\n"
            f"--- stdout ---\n{cmd.stdout}\n"
            f"--- stderr ---\n{cmd.stderr}\n"
        )
        result["returncode"] = cmd.returncode
        if not cmd.allowed:
            raise PatchError(f"command_blocked: {cmd.block_reason}")
        result["test_passed"] = cmd.returncode == 0
        if not result["test_passed"]:
            result["failure_reason"] = f"test_failed: returncode={cmd.returncode}"
        result["status"] = "passed" if (result["patch_applied"] and result["test_passed"]) else "failed"

    except PatchError as exc:
        result["failure_reason"] = str(exc)
        result["status"] = "failed"
    finally:
        result["error"] = result["failure_reason"]
        refs = _write_artifacts(artifacts_dir, diff_text, test_log, result)
        result.update(refs)
        if sandbox is not None:
            shutil.rmtree(sandbox, ignore_errors=True)

    return result


def _aggregate_diff(work: Path, originals: dict[str, str]) -> str:
    chunks = []
    for rel, original in originals.items():
        current = (work / rel).read_text(encoding="utf-8")
        if current == original:
            continue
        chunks.append(
            "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    current.splitlines(keepends=True),
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                )
            )
        )
    return "".join(chunks)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--test-command", default=None)
    parser.add_argument("--plans-dir", default=None)
    parser.add_argument("--artifacts-dir", default=None)
    parser.add_argument("--timeout-sec", type=int, default=60)
    args = parser.parse_args()
    print(json.dumps(
        patch_and_run(
            args.project_dir,
            test_command=args.test_command,
            artifacts_dir=args.artifacts_dir,
            plans_dir=args.plans_dir,
            timeout_sec=args.timeout_sec,
        ),
        ensure_ascii=False,
        indent=2,
    ))
