"""Plan validation — structural + safety checks over a declarative `Plan`.

The validator NEVER executes a step. It rejects plans that are structurally
broken (duplicate ids, dangling dependencies, illegal risk levels), or that try
to smuggle in direct shell execution or secret-looking input. A plan that fails
validation must not be handed to any executor.
"""
from __future__ import annotations

import json

from src.llm.redaction import redact_text
from src.planner.types import Plan, PlanValidationResult, RISK_LEVELS

# Skill names that would mean "run an arbitrary shell/eval directly" — the
# planner is never allowed to emit these. Only named, registered skills may run,
# and shell only ever happens *inside* a vetted skill (e.g. start_local_server),
# never as a raw planner-chosen command.
FORBIDDEN_SKILLS = {
    "raw_shell", "direct_command", "shell", "bash", "sh",
    "eval", "exec", "system", "subprocess", "os_system",
}

# Keys in a step's inputs that would smuggle a raw command past the skill layer.
FORBIDDEN_INPUT_KEYS = {"shell", "raw_command", "direct_command", "cmd", "command_line"}


def _contains_secret(text: str) -> bool:
    """True if redaction would change the text — i.e. a secret pattern is present."""
    return redact_text(text) != text


def validate_plan(plan: Plan) -> PlanValidationResult:
    errors: list[str] = []
    notes: list[str] = []

    if not isinstance(plan, Plan):
        return PlanValidationResult(valid=False, errors=["plan is not a Plan instance"])

    if not plan.steps:
        notes.append("plan has no steps")

    ids: list[str] = []
    for idx, step in enumerate(plan.steps):
        where = f"step[{idx}] id={step.id!r}"

        # id uniqueness
        if not step.id:
            errors.append(f"{where}: empty step id")
        elif step.id in ids:
            errors.append(f"{where}: duplicate step id {step.id!r}")
        ids.append(step.id)

        # skill non-empty
        if not step.skill or not str(step.skill).strip():
            errors.append(f"{where}: empty skill")

        # no direct shell / eval skills
        if str(step.skill).strip().lower() in FORBIDDEN_SKILLS:
            errors.append(f"{where}: forbidden direct-shell skill {step.skill!r}")

        # risk level legal
        if step.risk_level not in RISK_LEVELS:
            errors.append(
                f"{where}: illegal risk_level {step.risk_level!r} (expected one of {RISK_LEVELS})"
            )

        # high risk must require approval
        if step.risk_level == "high" and not step.requires_approval:
            errors.append(f"{where}: high risk step must set requires_approval=true")

        # forbidden input keys (raw command smuggling)
        bad_keys = set(map(str, step.inputs.keys())) & FORBIDDEN_INPUT_KEYS
        if bad_keys:
            errors.append(
                f"{where}: forbidden raw-command input key(s) {sorted(bad_keys)}"
            )

        # secret-looking inputs
        try:
            inputs_json = json.dumps(step.inputs, ensure_ascii=False, default=str)
        except Exception:  # noqa: BLE001
            inputs_json = str(step.inputs)
        if _contains_secret(inputs_json):
            # Never echo the offending value — report the location only.
            errors.append(f"{where}: inputs contain a secret-looking value")

    # depends_on must reference existing step ids
    id_set = set(ids)
    for idx, step in enumerate(plan.steps):
        for dep in step.depends_on:
            if dep not in id_set:
                errors.append(
                    f"step[{idx}] id={step.id!r}: depends_on missing step {dep!r}"
                )
            if dep == step.id:
                errors.append(f"step[{idx}] id={step.id!r}: step depends on itself")

    return PlanValidationResult(valid=not errors, errors=errors, notes=notes)
