"""Read-Only Plan Execution Gate v0 — human-approved, allowlisted, read-only only.

This is the controlled boundary between an *approved* review package and actually
running a plan. It is fail-closed and deliberately tiny:

  - It runs ONLY allowlisted, read-only skills (v0: `inspect_project`).
  - It refuses everything else outright — patch / server / browser / console / repair
    / apply / merge / staging / promotion / raw shell / eval — via an explicit denylist
    AND an allowlist (belt and suspenders).
  - It executes ONLY skills it has a vetted runner for (`SKILL_RUNNERS`); an
    allowlisted skill with no runner still cannot run.
  - The execution *context* (the `project_dir` to inspect) comes from a vetted operator
    input — NEVER from the model's plan inputs, browser/page content, or run traces.
  - It never replans, never auto-repairs, never starts a shell, and never bypasses the
    Safety Gate. inspect_project is a pure, read-only directory lister.
  - Every result is redacted before it leaves this module.

Authorization (ALL required for a real run): an explicit `approved=True` flag, an
approval checklist that contains `APPROVED_FOR_READONLY_EXECUTION: true`, a non-empty
reviewer, and a plan that passes both `PlanValidator` and this gate's read-only checks.
"""
from __future__ import annotations

import importlib.util
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.llm.redaction import redact_mapping, redact_text
from src.planner.plan_validator import validate_plan
from src.planner.types import Plan, PlanValidationResult

ROOT = Path(__file__).resolve().parents[2]

# Read-only allowlist — the ONLY skills this gate may execute. Expanded in
# Read-Only Skill Allowlist Expansion v0 to add the safe, content-free
# `list_project_files` (still no browser/server/patch/repair/promotion).
READONLY_ALLOWLIST = ("inspect_project", "list_project_files")

# Explicit denylist (defense in depth; also covered by allowlist + plan validator).
FORBIDDEN_SKILLS = (
    "patch_file_and_run_tests", "start_local_server", "open_localhost_browser",
    "read_browser_console", "repair", "repair_apply", "repair_merge", "apply",
    "merge", "staging_promote", "staging", "promote", "promotion",
    "raw_shell", "direct_command", "exec", "eval", "bash", "sh", "system",
    "subprocess", "python_exec", "arbitrary_tool",
)

APPROVAL_MARKER = "APPROVED_FOR_READONLY_EXECUTION: true"
# Approval is granted ONLY by a standalone marker LINE (optionally bulleted) — never
# by the substring appearing inside instructional prose (e.g. "edit the line to
# `APPROVED_FOR_READONLY_EXECUTION: true`"). This prevents a NOT-APPROVED checklist
# whose help text mentions the marker from being mis-read as approved.
APPROVAL_MARKER_RE = re.compile(
    r"(?im)^\s*-?\s*APPROVED_FOR_READONLY_EXECUTION\s*:\s*true\s*$")


@dataclass
class GateResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    allowed_steps: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return redact_mapping({"ok": self.ok, "errors": list(self.errors),
                               "allowed_steps": list(self.allowed_steps)})


@dataclass
class ApprovalRecord:
    approved_marker: bool = False
    reviewer: str = ""

    @property
    def reviewer_ok(self) -> bool:
        r = (self.reviewer or "").strip().lower()
        return bool(r) and r != "(none)"


class ReadOnlyExecutionError(Exception):
    """Raised when a read-only execution cannot proceed (fail closed)."""


def validate_readonly_plan(plan: Plan,
                           validation: PlanValidationResult | None = None) -> GateResult:
    """A plan is read-only-executable only when it passes PlanValidator AND every step
    is low-risk AND every step's skill is allowlisted (and not denylisted)."""
    if not isinstance(plan, Plan):
        return GateResult(ok=False, errors=["not_a_plan"])
    if validation is None:
        validation = validate_plan(plan)

    errors: list[str] = []
    if not validation.valid:
        errors.append("plan_not_validated")
        errors.extend(f"validation:{e}" for e in validation.errors)

    allowed: list[dict] = []
    if not plan.steps:
        errors.append("empty_plan")
    for s in plan.steps:
        skill = str(s.skill)
        if skill in FORBIDDEN_SKILLS:
            errors.append(f"forbidden_skill:{s.id}:{skill}")
            continue
        if skill not in READONLY_ALLOWLIST:
            errors.append(f"skill_not_readonly_allowlisted:{s.id}:{skill}")
            continue
        if s.risk_level != "low":
            errors.append(f"not_low_risk:{s.id}:{s.risk_level}")
            continue
        if skill not in SKILL_RUNNERS:
            errors.append(f"no_runner_for_skill:{s.id}:{skill}")
            continue
        allowed.append({"id": s.id, "skill": skill, "risk_level": s.risk_level})

    return GateResult(ok=not errors, errors=errors, allowed_steps=allowed)


def parse_approval(checklist_text: str) -> ApprovalRecord:
    """Parse the approval marker + reviewer from an approval_checklist.md. Reads only
    the provided text (the caller reads the file); never reads a secret file."""
    if not isinstance(checklist_text, str):
        return ApprovalRecord()
    # Match only a standalone marker LINE (not the substring inside help text).
    marker = bool(APPROVAL_MARKER_RE.search(checklist_text))
    reviewer = ""
    m = re.search(r"(?im)^\s*-?\s*reviewer:\s*(.+)\s*$", checklist_text)
    if m:
        reviewer = m.group(1).strip()
    return ApprovalRecord(approved_marker=marker, reviewer=reviewer)


def authorize(plan: Plan, approval: ApprovalRecord, *, approved: bool) -> GateResult:
    """All conditions must hold for a real read-only run (fail closed otherwise)."""
    gate = validate_readonly_plan(plan)
    errors = list(gate.errors)
    if not approved:
        errors.append("missing_--approved_flag")
    if not approval.approved_marker:
        errors.append("approval_checklist_missing_APPROVED_FOR_READONLY_EXECUTION_true")
    if not approval.reviewer_ok:
        errors.append("missing_or_empty_reviewer")
    return GateResult(ok=not errors, errors=errors, allowed_steps=gate.allowed_steps)


# --------------------------------------------------------------------------- #
# Vetted skill runners — the ONLY callables the gate may invoke. Each is read-only.
# The runner is given a vetted project_dir (operator input), NOT plan/model inputs.
# --------------------------------------------------------------------------- #
def _load_inspect_project():
    """Load the stable inspect_project function read-only (never modifies the skill)."""
    path = ROOT / "skills" / "inspect_project" / "scripts" / "inspect_project.py"
    spec = importlib.util.spec_from_file_location("inspect_project_skill", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.inspect_project


def _run_inspect_project(project_dir: str) -> dict:
    fn = _load_inspect_project()
    result = fn(str(project_dir))
    # Redact defensively (the result is a project listing — no secret expected).
    return redact_mapping(result)


# --- list_project_files: a safe, content-free, repo-relative path lister --- #
# Default cap on listed entries (keeps output small and bounded).
LIST_FILES_MAX = 200

# Directory names never listed/descended (anywhere in the tree).
EXCLUDED_DIR_NAMES = frozenset({
    ".git", ".venv", "venv", "runs", "__pycache__", ".pytest_cache", ".cache",
    "node_modules", "dist", "build", ".mypy_cache", ".ruff_cache",
    "ms-playwright", "screenshots", ".secrets", "secrets",
})

# Repo-relative paths never listed (exact match).
EXCLUDED_RELPATHS = frozenset({
    ".env", "config/config.json", "password_and_api.txt",
})

# File-name globs never listed (secret-looking / credential-like / artifacts).
EXCLUDED_NAME_GLOBS = (
    ".env", ".env.*", "*.env", "password*.txt", "passwords*", "*.pem", "*.key",
    "*.p12", "*.pfx", "id_rsa", "id_ed25519", "*.token", "secrets.*",
    "*secret*.txt", "*secret*.json", "*secret*.yaml", "*secret*.yml",
    "*credentials*.json", "*credentials*.txt", "*.png", "*.jpg", "*.jpeg",
    "*.gif", "*.webp",  # screenshots / images
)


def _is_excluded_name(name: str) -> bool:
    import fnmatch
    return any(fnmatch.fnmatch(name, g) for g in EXCLUDED_NAME_GLOBS)


def list_project_files(project_dir: str, *, max_files: int = LIST_FILES_MAX) -> dict:
    """List repo-relative paths under project_dir with basic metadata ONLY.

    Read-only and content-free: it NEVER opens or reads a file's contents — only the
    relative path, whether it's a directory, and the byte size from stat. It excludes
    VCS/venv/cache/build dirs, screenshots, and secret-looking / config / .env /
    password files, and it NEVER follows a symlink that escapes the root. Output is
    capped at `max_files` and redacted by the caller-facing path.
    """
    root = Path(project_dir)
    root_resolved = root.resolve()
    if not root.exists() or not root.is_dir():
        return {"status": "failed", "error": "directory_not_found"}

    listed: list[dict] = []
    excluded_count = 0
    truncated = False

    # os.walk with topdown so we can prune excluded directories in-place.
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        # Prune excluded directory names before descending.
        kept_dirs = []
        for d in list(dirnames):
            if d in EXCLUDED_DIR_NAMES:
                excluded_count += 1
                continue
            full = Path(dirpath) / d
            # Never follow a symlink that escapes the repo root.
            if full.is_symlink():
                try:
                    full.resolve().relative_to(root_resolved)
                except (ValueError, OSError):
                    excluded_count += 1
                    continue
            kept_dirs.append(d)
        dirnames[:] = kept_dirs

        for d in dirnames:
            full = Path(dirpath) / d
            rel = full.relative_to(root).as_posix()
            if rel in EXCLUDED_RELPATHS:
                excluded_count += 1
                continue
            if len(listed) >= max_files:
                truncated = True
                break
            listed.append({"path": rel, "is_dir": True, "size": None})

        for f in filenames:
            rel = (Path(dirpath) / f).relative_to(root).as_posix()
            if rel in EXCLUDED_RELPATHS or _is_excluded_name(f):
                excluded_count += 1
                continue
            full = Path(dirpath) / f
            if full.is_symlink():
                try:
                    full.resolve().relative_to(root_resolved)
                except (ValueError, OSError):
                    excluded_count += 1
                    continue
            if len(listed) >= max_files:
                truncated = True
                break
            try:
                size = full.stat().st_size  # metadata only — NO content read
            except OSError:
                size = None
            listed.append({"path": rel, "is_dir": False, "size": size})
        if truncated:
            break

    listed.sort(key=lambda e: e["path"])
    return {
        "status": "ok",
        "skill": "list_project_files",
        "content_read": False,          # invariant: never reads file contents
        "file_count": len(listed),
        "max_files": max_files,
        "truncated": truncated,
        "excluded_count": excluded_count,
        "files": listed,
        "notes": [],
    }


def _run_list_project_files(project_dir: str) -> dict:
    # Redact defensively (paths only — no content, no secret expected).
    return redact_mapping(list_project_files(str(project_dir)))


SKILL_RUNNERS = {
    "inspect_project": _run_inspect_project,
    "list_project_files": _run_list_project_files,
}


def execute_readonly_plan(plan: Plan, approval: ApprovalRecord, *, approved: bool,
                          project_dir: str) -> dict:
    """Execute an APPROVED read-only plan over a VETTED project_dir, running its
    allowlisted read-only steps IN ORDER (plan order). Fail-closed: if authorization
    fails, OR any step's runner reports a non-ok status, it raises
    ReadOnlyExecutionError and stops — it NEVER retries, replans, or auto-repairs.
    Returns a redacted result that records the execution order. Never runs a shell."""
    auth = authorize(plan, approval, approved=approved)
    if not auth.ok:
        raise ReadOnlyExecutionError("; ".join(auth.errors) or "unauthorized")

    results = []
    execution_order = []  # ordered [{order, id, skill}] — the exact sequence run
    for idx, step in enumerate(auth.allowed_steps):
        runner = SKILL_RUNNERS.get(step["skill"])
        if runner is None:  # unreachable (validate_readonly_plan checks), but fail closed
            raise ReadOnlyExecutionError(f"no_runner_for_skill:{step['skill']}")
        out = runner(project_dir)
        status = out.get("status", "unknown")
        execution_order.append({"order": idx, "id": step["id"], "skill": step["skill"]})
        results.append({"id": step["id"], "skill": step["skill"],
                        "status": status, "result": out})
        # Fail closed on the first failing step — no retry, no replan, no repair.
        if status != "ok":
            raise ReadOnlyExecutionError(
                f"step_failed:{step['id']}:{step['skill']}:{status}")

    return redact_mapping({
        "executed": True,
        "read_only": True,
        "auto_repair": False,
        "replanned": False,
        "retried": False,
        "project_dir": str(project_dir),
        "steps_executed": len(results),
        "execution_order": execution_order,
        "executed_skills_in_order": [e["skill"] for e in execution_order],
        "results": results,
    })
