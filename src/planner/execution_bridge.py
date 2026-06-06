"""Plan execution bridge — turn a *validated* plan into a controlled, allowlisted
skill sequence the existing orchestrator can run.

This bridge is deliberately NOT a general autonomous agent. It:

- refuses any plan that did not pass validation (`PlanValidationResult.valid`);
- allows ONLY a fixed allowlist of skills (no raw shell / eval / arbitrary tool);
- enforces an approval policy (high-risk steps need explicit approval);
- never mutates the plan, never calls an LLM, never runs a shell command itself,
  and never bypasses the Safety Gate (the orchestrator still safety-checks every
  command the skills emit);
- supplies execution *context* (fixture / patch_plan / start_command) only from a
  fixed per-marker registry — the planner never supplies shell commands.

See `specs/planner/plan_execution_bridge_contract.md`.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

from src.llm.redaction import redact_mapping
from src.planner.plan_validator import validate_plan
from src.planner.types import Plan, PlanValidationResult

# First-version allowlist. Only these skills may be executed via a plan.
ALLOWLISTED_SKILLS = (
    "inspect_project",
    "start_local_server",
    "open_localhost_browser",
    "read_browser_console",
    "patch_file_and_run_tests",
)

# Explicit denylist (also covered by the plan validator). Belt and suspenders:
# even if validation were skipped, the bridge refuses these outright.
FORBIDDEN_SKILLS = (
    "raw_shell",
    "direct_command",
    "eval",
    "exec",
    "bash",
    "python_exec",
    "arbitrary_tool",
)


@dataclass
class BridgeStep:
    """One executable step: the plan step + the eval-runner alias it maps to."""

    plan_step_id: str
    skill: str
    alias: str
    risk_level: str
    requires_approval: bool

    def to_dict(self) -> dict:
        return {
            "plan_step_id": self.plan_step_id,
            "skill": self.skill,
            "alias": self.alias,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
        }


@dataclass
class BridgeResult:
    """Outcome of bridging a plan. `ok` is True only when there are no errors."""

    ok: bool
    errors: list[str] = field(default_factory=list)
    steps: list[BridgeStep] = field(default_factory=list)
    required_skills: list[dict] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    approved_high_risk: bool = False

    def to_dict(self) -> dict:
        # Redacted by construction — none of these fields carry secrets, but we
        # pass through redaction so this is always safe to write to a trace.
        return redact_mapping({
            "ok": self.ok,
            "errors": list(self.errors),
            "steps": [s.to_dict() for s in self.steps],
            "required_skills": list(self.required_skills),
            "risk_notes": list(self.risk_notes),
            "approved_high_risk": self.approved_high_risk,
        })


class PlanExecutionError(Exception):
    """Raised when a plan cannot be turned into a safe executable sequence."""


def _alias_for(skill: str, step_id: str, counts: dict[str, int]) -> str:
    """A skill that appears once keeps its name (matches the existing eval
    chains); a skill that repeats uses the plan step id (e.g. open_pre/open_post)
    so the orchestrator's phase-aware evidence rules line up."""
    return skill if counts.get(skill, 0) == 1 else step_id


def build_execution_sequence(
    plan: Plan,
    validation: PlanValidationResult | None = None,
    *,
    approve_high_risk: bool = False,
) -> BridgeResult:
    """Convert a validated plan into an allowlisted, approval-checked sequence.

    The input plan is never mutated. Returns a `BridgeResult`; when `ok` is False
    the plan must NOT be executed (fail closed).
    """
    if not isinstance(plan, Plan):
        return BridgeResult(ok=False, errors=["not_a_plan"])

    # Validate here if the caller did not (never execute an unvalidated plan).
    if validation is None:
        validation = validate_plan(plan)

    errors: list[str] = []
    if not validation.valid:
        errors.append("plan_not_validated")
        # Surface the underlying validation errors too (already secret-safe).
        errors.extend(f"validation:{e}" for e in validation.errors)

    counts: dict[str, int] = {}
    for ps in plan.steps:
        counts[ps.skill] = counts.get(ps.skill, 0) + 1

    steps: list[BridgeStep] = []
    required: list[dict] = []
    risk_notes: list[str] = []

    for ps in plan.steps:
        skill = ps.skill
        if skill in FORBIDDEN_SKILLS:
            errors.append(f"forbidden_skill:{ps.id}:{skill}")
            continue
        if skill not in ALLOWLISTED_SKILLS:
            errors.append(f"skill_not_allowlisted:{ps.id}:{skill}")
            continue
        if ps.risk_level == "high" and not (ps.requires_approval and approve_high_risk):
            errors.append(f"high_risk_without_approval:{ps.id}")
            continue
        if ps.risk_level == "medium":
            risk_notes.append(f"medium_risk:{ps.id}:{skill}")

        alias = _alias_for(skill, ps.id, counts)
        steps.append(BridgeStep(ps.id, skill, alias, ps.risk_level, ps.requires_approval))
        required.append({"skill": skill, "as": alias})

    ok = not errors
    return BridgeResult(
        ok=ok,
        errors=errors,
        steps=steps,
        required_skills=required,
        risk_notes=risk_notes,
        approved_high_risk=bool(approve_high_risk),
    )


# --------------------------------------------------------------------------- #
# Execution-context registry — keyed by the fake planner's deterministic marker.
# The *plan* stays declarative; the concrete fixture / patch_plan / start_command
# needed to actually run the allowlisted skills live here, NOT in planner output.
# This is what keeps the planner from ever supplying a shell command: execution
# context is a fixed, vetted template, not free-form planner text.
# --------------------------------------------------------------------------- #

# The login.py source fix, shared by the patch + full-browser contexts (mirrors
# evals/browser/full_browser_vite_login_bug_e2e.yaml — no secret material).
_LOGIN_DIFF = (
    "--- a/login.py\n"
    "+++ b/login.py\n"
    "@@ -1,3 +1,3 @@\n"
    " def login_token(user):\n"
    "     # Bug: returns the raw user instead of the user's token.\n"
    "-    return user\n"
    "+    return user[\"token\"]\n"
)

_PATCH_PLAN = {
    "test_command": "python3 test_login.py",
    "patches": [{"type": "unified_diff", "file": "login.py", "diff": _LOGIN_DIFF}],
}

_FULL_BROWSER_CONTEXT = {
    "fixture": {"path": "fixtures/vite_login_bug_browser"},
    "start_command": "node server.js",
    "keep_alive": True,
    "server_timeout_sec": 25,
    "browser_timeout_sec": 20,
    "browser_mode": "playwright",
    "require_real_browser": True,
    "wait_after_load_ms": 400,
    "test_command": "python3 test_login.py",
    "patch_plan": _PATCH_PLAN,
    # Inner (real skill-evidence) criteria used to derive the underlying score.
    "inner_success_criteria": [
        "server_started",
        "real_browser_page_loaded",
        "console_error_collected",
        "patch_applied",
        "tests_pass",
        "browser_reverify_passed",
        "no_fatal_console_error_after_patch",
        "no_lingering_server_process",
    ],
}

_PATCH_ONLY_CONTEXT = {
    "fixture": {"path": "fixtures/vite_login_bug_browser"},
    "test_command": "python3 test_login.py",
    "patch_plan": _PATCH_PLAN,
    "inner_success_criteria": [
        "project_inspected",
        "source_file_patched",
        "tests_pass",
    ],
}

_EXECUTION_CONTEXTS = {
    "FAKE_PLAN_FULL_BROWSER_E2E": _FULL_BROWSER_CONTEXT,
    "FAKE_PLAN_PATCH_ONLY": _PATCH_ONLY_CONTEXT,
}


def execution_context_for(marker: str) -> dict:
    """Return a deep copy of the vetted execution context for a marker, or {}.

    An unknown marker returns {} — there is no execution context, so the bridge
    cannot run it. Only the fake planner's known markers are executable."""
    return copy.deepcopy(_EXECUTION_CONTEXTS.get(marker or "", {}))


def executable_markers() -> tuple[str, ...]:
    return tuple(_EXECUTION_CONTEXTS.keys())
