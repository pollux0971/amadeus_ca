"""Staging report rendering — safe, redacted markdown for a staging promotion workspace.

Every string passes through redaction. The report is clearly marked as a
staging-workspace-only, stable-untouched, not-stable-promoted artifact that still
needs human review before stable, records whether the rollback was verified, and
notes the promotion policy is still required.
"""
from __future__ import annotations

from src.llm.redaction import redact_text


def banner_lines(rollback_verified: bool) -> tuple[str, ...]:
    return (
        "STAGING WORKSPACE ONLY",
        "STABLE UNTOUCHED",
        "NOT STABLE PROMOTED",
        "HUMAN REVIEW REQUIRED BEFORE STABLE",
        "ROLLBACK VERIFIED" if rollback_verified else "ROLLBACK NEEDS REVIEW",
        "PROMOTION POLICY STILL REQUIRED",
    )


def render_staging_report(manifest, validation, regression_results: dict | None = None) -> str:
    rollback_verified = bool(manifest.get("rollback_verified"))
    lines = ["# Staging Report", ""]
    for b in banner_lines(rollback_verified):
        lines.append(f"> **{b}**")
    lines += [
        "",
        f"- staging id: {redact_text(str(manifest.get('staging_id', '')))}",
        f"- source merge workspace: {redact_text(str(manifest.get('source_merge_workspace', '')))}",
        f"- reviewer: {redact_text(str(manifest.get('reviewer', ''))) or '(none)'}",
        f"- staged: **{manifest.get('staged')}**",
        f"- stable modified: **{manifest.get('stable_modified')}**",
        f"- stable promoted: **{manifest.get('stable_promoted')}**",
        f"- active candidate modified: **{manifest.get('active_candidate_modified')}**",
        f"- rollback verified: **{rollback_verified}**",
    ]
    if validation is not None:
        lines.append(f"- staging validation passed: **{validation.valid}**")
        if getattr(validation, "errors", None):
            lines.append("- validation errors:")
            for e in validation.errors:
                lines.append(f"  - {redact_text(str(e))}")

    lines += ["", "## Staged changes (in this staging workspace only)"]
    for f in manifest.get("staged_files", []) or []:
        lines.append(f"- `{redact_text(str(f))}`")

    lines += ["", "## Targeted tests + regression (fixed allowlist)"]
    executed = bool((regression_results or {}).get("executed"))
    lines.append(f"- executed: **{executed}**")
    lines.append("- targeted:")
    for c in manifest.get("targeted_tests", []) or []:
        lines.append(f"  - `{redact_text(str(c))}`")
    lines.append("- regression:")
    for c in manifest.get("regression_tests", []) or []:
        lines.append(f"  - `{redact_text(str(c))}`")
    if executed and (regression_results or {}).get("results"):
        lines += ["", "| command | ok | exit |", "| --- | --- | --- |"]
        for r in regression_results["results"]:
            lines.append(f"| `{redact_text(str(r.get('command')))}` | {r.get('ok')} "
                         f"| {r.get('exit')} |")

    lines += [
        "",
        "> This staging promotion lands ONLY in a staging workspace. No repo target",
        "> file, active candidate, stable skill, safety gate, or promotion policy is",
        "> modified, and nothing is stable-promoted. The promotion policy review and a",
        "> human sign-off are still required before any stable move.",
    ]
    return "\n".join(lines) + "\n"
