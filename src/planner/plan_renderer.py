"""Plan rendering — safe, redacted markdown / json summaries of a plan.

Every string that leaves this module passes through redaction, so no
secret-looking value can ever reach a terminal, trace, or report. The renderer
shows each step's skill, dependencies, risk, approval flag, and success criteria.
"""
from __future__ import annotations

import json

from src.llm.redaction import redact_mapping, redact_text
from src.planner.types import Plan, PlanValidationResult


def render_json(plan: Plan, validation: PlanValidationResult | None = None) -> str:
    """Return a redacted JSON document for the plan (and optional validation)."""
    doc = {"plan": redact_mapping(plan.to_dict())}
    if validation is not None:
        doc["validation"] = redact_mapping(validation.to_dict())
    return json.dumps(doc, ensure_ascii=False, indent=2)


def render_markdown(plan: Plan, validation: PlanValidationResult | None = None) -> str:
    """Return a redacted markdown summary of the plan (and optional validation)."""
    lines: list[str] = []
    lines.append("# Plan")
    lines.append("")
    lines.append(f"- goal: {redact_text(plan.goal)}")
    lines.append(f"- marker: {redact_text(plan.marker) or '(none)'}")
    lines.append(f"- steps: {len(plan.steps)}")
    if validation is not None:
        lines.append(f"- valid: {validation.valid}")
        if validation.errors:
            lines.append("- validation errors:")
            for e in validation.errors:
                lines.append(f"  - {redact_text(str(e))}")
    lines.append("")
    lines.append("| id | skill | depends_on | risk | approval | success_criteria |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for step in plan.steps:
        deps = ", ".join(step.depends_on) or "-"
        crit = ", ".join(step.success_criteria) or "-"
        lines.append(
            f"| {redact_text(step.id)} | {redact_text(step.skill)} | {redact_text(deps)} "
            f"| {step.risk_level} | {'yes' if step.requires_approval else 'no'} "
            f"| {redact_text(crit)} |"
        )
    lines.append("")
    lines.append("> Plan only — the planner never executes these steps.")
    return "\n".join(lines) + "\n"
