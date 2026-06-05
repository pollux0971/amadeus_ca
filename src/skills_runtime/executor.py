from __future__ import annotations

import importlib.util
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .loader import SkillPackage, discover_skills


# Skills whose public entry function name differs from the skill_id.
#
# This adapter table lives in the harness so that stable skill packages are
# NOT modified (CLAUDE.md rule #1). New skills should prefer one of the
# resolution paths in `_load_callable` that do not need an alias: name the
# entry function == skill_id, expose a module-level `run()`, or declare
# `entrypoint.callable` in manifest.yaml.
CALLABLE_ALIASES: dict[str, str] = {
    "start_local_server": "simulate_start_server",
    "read_browser_console": "summarize_console",
    "patch_file_and_run_tests": "simulate_patch_and_test",
}

# Output `status` values that indicate the skill itself reported failure.
_FAILURE_STATUSES = {"failed", "error", "not_implemented"}


@dataclass
class SkillResult:
    """Normalized result of executing a single skill."""

    skill_id: str
    ok: bool
    output: dict
    error: str | None = None
    used_inputs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "ok": self.ok,
            "output": self.output,
            "error": self.error,
            "used_inputs": self.used_inputs,
        }


class SkillExecutionError(Exception):
    """Raised for harness-level problems (unknown skill, no entrypoint)."""


class SkillExecutor:
    """Loads and runs skill packages by their declared entrypoint.

    The executor never trusts arbitrary input: it binds only the inputs that
    the entry function actually declares (via ``inspect.signature``), reports
    missing required inputs instead of raising, and converts any exception
    raised inside a skill into a failed :class:`SkillResult` so a single bad
    skill cannot crash the orchestration loop.
    """

    def __init__(self, skills_dir: str | Path = "skills"):
        self.skills_dir = Path(skills_dir)
        self._packages: dict[str, SkillPackage] = {
            pkg.skill_id: pkg for pkg in discover_skills(self.skills_dir)
        }
        self._callable_cache: dict[str, Callable[..., Any]] = {}

    # -- discovery -----------------------------------------------------------

    def available_skills(self) -> list[str]:
        return sorted(self._packages)

    def get_package(self, skill_id: str) -> SkillPackage:
        if skill_id not in self._packages:
            raise SkillExecutionError(f"unknown skill: {skill_id}")
        return self._packages[skill_id]

    # -- loading -------------------------------------------------------------

    def _load_callable(self, skill_id: str) -> Callable[..., Any]:
        if skill_id in self._callable_cache:
            return self._callable_cache[skill_id]

        pkg = self.get_package(skill_id)
        entrypoint = pkg.manifest.get("entrypoint") or {}
        rel_path = entrypoint.get("path")
        if not rel_path:
            raise SkillExecutionError(f"{skill_id}: manifest has no entrypoint.path")

        script_path = pkg.root / rel_path
        if not script_path.exists():
            raise SkillExecutionError(f"{skill_id}: entrypoint not found: {script_path}")

        spec = importlib.util.spec_from_file_location(f"skill_{skill_id}", script_path)
        if spec is None or spec.loader is None:
            raise SkillExecutionError(f"{skill_id}: cannot load module from {script_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Resolution order, most explicit first.
        candidates = [
            entrypoint.get("callable"),
            CALLABLE_ALIASES.get(skill_id),
            skill_id,
            "run",
        ]
        for name in candidates:
            if name and callable(getattr(module, name, None)):
                fn = getattr(module, name)
                self._callable_cache[skill_id] = fn
                return fn

        tried = [c for c in candidates if c]
        raise SkillExecutionError(
            f"{skill_id}: no entry callable found (tried {tried})"
        )

    # -- execution -----------------------------------------------------------

    def run(self, skill_id: str, inputs: dict | None = None) -> SkillResult:
        inputs = dict(inputs or {})

        try:
            fn = self._load_callable(skill_id)
        except SkillExecutionError as exc:
            return SkillResult(skill_id, ok=False, output={}, error=str(exc), used_inputs=inputs)

        sig = inspect.signature(fn)
        accepts_var_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        if accepts_var_kwargs:
            bound = dict(inputs)
        else:
            bound = {k: v for k, v in inputs.items() if k in sig.parameters}

        missing = [
            name
            for name, p in sig.parameters.items()
            if p.default is inspect.Parameter.empty
            and p.kind
            in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
            and name not in bound
        ]
        if missing:
            return SkillResult(
                skill_id,
                ok=False,
                output={},
                error=f"missing required inputs: {missing}",
                used_inputs=bound,
            )

        try:
            result = fn(**bound)
        except Exception as exc:  # noqa: BLE001 - a skill failure must not crash the loop
            return SkillResult(
                skill_id,
                ok=False,
                output={},
                error=f"{type(exc).__name__}: {exc}",
                used_inputs=bound,
            )

        if not isinstance(result, dict):
            result = {"value": result}

        ok = result.get("status") not in _FAILURE_STATUSES
        return SkillResult(skill_id, ok=ok, output=result, used_inputs=bound)
