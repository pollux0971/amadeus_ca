"""Candidate workspace — write a repair proposal as a human-reviewable draft.

This writes proposal artifacts into a workspace directory. It NEVER touches a
target file, applies a patch, runs a test, or promotes anything. The workspace is
purely a place for a human to read the proposal and an approval checklist.
"""
from __future__ import annotations

from pathlib import Path

from src.repair.proposal_renderer import BANNER, render_json, render_markdown
from src.repair.types import CandidateWorkspacePlan

# Default base for proposal workspaces (inside candidates, clearly namespaced as
# proposals — not a candidate skill itself).
DEFAULT_BASE = "harnesses/candidates/_repair_proposals"


def _readme(proposal_id: str) -> str:
    return (
        f"# Repair proposal workspace — `{proposal_id}`\n\n"
        f"> **{BANNER}**\n\n"
        "This directory holds a **repair proposal only**. Nothing here has been\n"
        "applied, executed, or promoted. The files are for human review:\n\n"
        "- `repair_proposal.md` / `repair_proposal.json` — the proposed changes\n"
        "  (redacted; allowlisted action types and target roots only).\n"
        "- `failure_analysis.json` — the classified failure this responds to.\n"
        "- `approval_checklist.md` — the gate a human must clear before any apply.\n\n"
        "**No target file was modified.** Applying a proposal is a separate,\n"
        "not-yet-implemented, human-approved step (`specs/repair/repair_loop_contract.md`).\n"
    )


def _approval_checklist(proposal, validation) -> str:
    lines = [
        "# Approval checklist (must be cleared by a human before any apply)",
        "",
        f"> **{BANNER}**",
        "",
        f"- proposal id: `{proposal.id}`",
        f"- failure_type: `{proposal.failure_type}`",
        f"- validation passed: **{validation.valid}**",
        "",
        "## Required sign-offs",
        "",
        "- [ ] A human reviewed every proposed action and target.",
        "- [ ] No action targets a stable skill, the safety gate, or the promotion policy.",
        "- [ ] No action is a raw shell / direct command / delete.",
        "- [ ] All targets stay inside the allowed roots (candidates/tests/evals/docs/reports).",
        "- [ ] High-risk actions have explicit approval.",
        "- [ ] The proposal contains no secret.",
        "- [ ] The change will be made in a candidate workspace, NOT in stable.",
        "- [ ] Promotion (if any) follows `specs/harness/promotion_policy.md` separately.",
        "",
        "## Proposed actions",
    ]
    for a in proposal.actions:
        lines.append(f"- [ ] `{a.id}` {a.action_type} → `{a.target}` "
                     f"(risk={a.risk_level}, approval={'yes' if a.requires_approval else 'no'})")
    lines += [
        "",
        "> Checking these boxes is a human action. This file does not apply anything.",
    ]
    return "\n".join(lines) + "\n"


def create_workspace(proposal, analysis, validation, *, base_dir: str | Path,
                     proposal_id: str | None = None) -> CandidateWorkspacePlan:
    """Write proposal artifacts under `base_dir/<proposal_id>/`. No target touched.

    Returns a `CandidateWorkspacePlan`. Raises nothing destructive — it only
    creates the workspace directory and writes redacted files.
    """
    pid = proposal_id or proposal.id
    workspace = Path(base_dir) / pid
    workspace.mkdir(parents=True, exist_ok=True)

    files: list[str] = []

    def _write(name: str, text: str) -> None:
        (workspace / name).write_text(text, encoding="utf-8")
        files.append(name)

    # All renderers/serializers redact; nothing secret reaches disk.
    _write("repair_proposal.json", render_json(proposal, validation))
    _write("repair_proposal.md", render_markdown(proposal, validation))
    import json as _json
    from src.llm.redaction import redact_mapping
    _write("failure_analysis.json",
           _json.dumps(redact_mapping(analysis.to_dict()), ensure_ascii=False, indent=2))
    _write("approval_checklist.md", _approval_checklist(proposal, validation))
    _write("README.md", _readme(pid))

    return CandidateWorkspacePlan(
        proposal_id=pid, workspace_dir=str(workspace), files_written=files, applied=False)
