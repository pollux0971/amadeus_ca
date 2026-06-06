"""Repair proposal rendering — safe, redacted markdown / json.

Every string that leaves this module passes through redaction. Each rendered
proposal is clearly marked PROPOSAL ONLY / NOT APPLIED / HUMAN APPROVAL REQUIRED
so it can never be mistaken for an applied change.
"""
from __future__ import annotations

import json

from src.llm.redaction import redact_mapping, redact_text
from src.repair.types import RepairProposal, RepairValidationResult

BANNER = "PROPOSAL ONLY — NOT APPLIED — HUMAN APPROVAL REQUIRED"


def render_json(proposal: RepairProposal,
                validation: RepairValidationResult | None = None) -> str:
    doc = {
        "banner": BANNER,
        "applied": False,
        "proposal": redact_mapping(proposal.to_dict()),
    }
    if validation is not None:
        doc["validation"] = redact_mapping(validation.to_dict())
    return json.dumps(doc, ensure_ascii=False, indent=2)


def render_markdown(proposal: RepairProposal,
                    validation: RepairValidationResult | None = None) -> str:
    lines = [
        "# Repair Proposal",
        "",
        f"> **{BANNER}**",
        "",
        f"- proposal id: {redact_text(proposal.id)}",
        f"- failure_type: {redact_text(proposal.failure_type)}",
        f"- marker: {redact_text(proposal.marker) or '(none)'}",
        f"- applied: **false**",
    ]
    if validation is not None:
        lines.append(f"- valid: {validation.valid}")
        if validation.errors:
            lines.append("- validation errors:")
            for e in validation.errors:
                lines.append(f"  - {redact_text(str(e))}")
    lines += [
        "",
        f"**Rationale:** {redact_text(proposal.rationale)}",
        "",
        "| id | action_type | target | risk | approval | tests_to_run |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for a in proposal.actions:
        tests = ", ".join(a.tests_to_run) or "-"
        lines.append(
            f"| {redact_text(a.id)} | {redact_text(a.action_type)} | {redact_text(a.target)} "
            f"| {a.risk_level} | {'yes' if a.requires_approval else 'no'} | {redact_text(tests)} |")
    lines += [
        "",
        "## Action reasons",
    ]
    for a in proposal.actions:
        lines.append(f"- **{redact_text(a.id)}** ({redact_text(a.action_type)}): "
                     f"{redact_text(a.reason)}")
    lines += [
        "",
        "> This is a proposal only. Nothing here is applied, executed, or promoted.",
        "> A human must review and approve before any change is made.",
    ]
    return "\n".join(lines) + "\n"
