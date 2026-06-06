"""Apply report rendering — safe, redacted markdown for an apply workspace.

Every string passes through redaction. The report is clearly marked as a
workspace-only, not-promoted, stable-untouched artifact that still needs human
review before any merge or promotion.
"""
from __future__ import annotations

from src.llm.redaction import redact_text

BANNER_LINES = (
    "APPROVED APPLICATION WORKSPACE ONLY",
    "NOT PROMOTED",
    "STABLE UNTOUCHED",
    "HUMAN REVIEW STILL REQUIRED FOR MERGE/PROMOTION",
)


def render_apply_report(manifest, validation, test_results: dict | None = None) -> str:
    lines = ["# Apply Report", ""]
    for b in BANNER_LINES:
        lines.append(f"> **{b}**")
    lines += [
        "",
        f"- apply id: {redact_text(manifest.apply_id)}",
        f"- proposal id: {redact_text(manifest.proposal_id)}",
        f"- approved by: {redact_text(manifest.approved_by) or '(none)'}",
        f"- promoted: **{manifest.promoted}**",
        f"- stable modified: **{manifest.stable_modified}**",
    ]
    if validation is not None:
        lines.append(f"- apply validation passed: **{validation.valid}**")
        if getattr(validation, "errors", None):
            lines.append("- validation errors:")
            for e in validation.errors:
                lines.append(f"  - {redact_text(str(e))}")
    lines += [
        "",
        "## Proposed changes (in this workspace only)",
        "| action id | action_type | intended target | proposed file |",
        "| --- | --- | --- | --- |",
    ]
    for a in manifest.actions:
        pf = a.get("proposed_file") or "(none — noop)"
        lines.append(f"| {redact_text(str(a.get('id')))} | {redact_text(str(a.get('action_type')))} "
                     f"| {redact_text(str(a.get('target')))} | {redact_text(str(pf))} |")

    lines += ["", "## Targeted tests (fixed allowlist)"]
    executed = bool((test_results or {}).get("executed"))
    lines.append(f"- executed: **{executed}**")
    for c in manifest.test_commands:
        lines.append(f"  - `{redact_text(c)}`")
    if executed and (test_results or {}).get("results"):
        lines.append("")
        lines.append("| command | ok | exit |")
        lines.append("| --- | --- | --- |")
        for r in test_results["results"]:
            lines.append(f"| `{redact_text(str(r.get('command')))}` | {r.get('ok')} "
                         f"| {r.get('exit')} |")

    lines += [
        "",
        "> This apply workspace modifies no repo target file, promotes nothing, and",
        "> touches no stable skill / safety gate / promotion policy. A human must",
        "> review and merge separately; merge and promotion are future phases.",
    ]
    return "\n".join(lines) + "\n"
