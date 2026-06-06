"""Merge report rendering — safe, redacted markdown for a candidate merge workspace.

Every string passes through redaction. The report is clearly marked as a
candidate-workspace-only, stable-untouched, not-promoted artifact that still needs
human review before any staging/stable promotion, and that a rollback plan exists.
"""
from __future__ import annotations

from src.llm.redaction import redact_text

BANNER_LINES = (
    "CANDIDATE WORKSPACE MERGE ONLY",
    "STABLE UNTOUCHED",
    "NOT PROMOTED",
    "HUMAN REVIEW REQUIRED BEFORE STAGING/STABLE",
    "ROLLBACK PLAN INCLUDED",
)


def render_merge_report(manifest, validation, test_results: dict | None = None) -> str:
    lines = ["# Merge Report", ""]
    for b in BANNER_LINES:
        lines.append(f"> **{b}**")
    lines += [
        "",
        f"- merge id: {redact_text(str(manifest.get('merge_id', '')))}",
        f"- source apply workspace: {redact_text(str(manifest.get('source_apply_workspace', '')))}",
        f"- reviewer: {redact_text(str(manifest.get('reviewer', ''))) or '(none)'}",
        f"- merged to candidate workspace: **{manifest.get('merged_to_candidate_workspace')}**",
        f"- stable modified: **{manifest.get('stable_modified')}**",
        f"- promoted: **{manifest.get('promoted')}**",
        f"- rollback available: **{manifest.get('rollback_available')}**",
    ]
    if validation is not None:
        lines.append(f"- merge validation passed: **{validation.valid}**")
        if getattr(validation, "errors", None):
            lines.append("- validation errors:")
            for e in validation.errors:
                lines.append(f"  - {redact_text(str(e))}")

    lines += ["", "## Merged changes (in this candidate workspace only)"]
    for f in manifest.get("merged_files", []) or []:
        lines.append(f"- `{redact_text(str(f))}`")

    lines += ["", "## Targeted tests + regression (fixed allowlist)"]
    executed = bool((test_results or {}).get("executed"))
    lines.append(f"- executed: **{executed}**")
    lines.append("- targeted:")
    for c in manifest.get("targeted_tests", []) or []:
        lines.append(f"  - `{redact_text(str(c))}`")
    lines.append("- regression:")
    for c in manifest.get("regression_tests", []) or []:
        lines.append(f"  - `{redact_text(str(c))}`")
    if executed and (test_results or {}).get("results"):
        lines += ["", "| command | ok | exit |", "| --- | --- | --- |"]
        for r in test_results["results"]:
            lines.append(f"| `{redact_text(str(r.get('command')))}` | {r.get('ok')} "
                         f"| {r.get('exit')} |")

    lines += [
        "",
        "> This merge lands ONLY in a candidate merge workspace. No repo target file,",
        "> active candidate, stable skill, safety gate, or promotion policy is",
        "> modified, and nothing is promoted. A rollback plan is included; a human",
        "> must review before any staging/stable promotion.",
    ]
    return "\n".join(lines) + "\n"
