"""Apply validation — gate a repair proposal for workspace-only application.

This is the stricter gate that must pass before a proposal may be materialized
into an apply workspace. On top of the proposal validator it requires an explicit
human approval marker + a named reviewer, and restricts apply to a subset of
action types. It NEVER applies anything; it only decides whether apply is allowed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from src.llm.redaction import redact_text
from src.repair.proposal_validator import (
    ACTION_DENYLIST,
    _contains_secret,
    _target_allowed,
    validate_proposal,
)
from src.repair.types import RepairProposal, RepairValidationResult

# The approval marker a human must place in approval_checklist.md.
APPROVAL_MARKER = "APPROVED_FOR_CANDIDATE_WORKSPACE_APPLY"

# v0 may apply only this subset of action types (noop is recorded, not applied).
APPLY_ACTION_ALLOWLIST = (
    "update_candidate", "add_test", "update_eval", "update_docs", "noop",
)


@dataclass
class ApprovalRecord:
    """Parsed human approval from an approval_checklist.md."""

    approved: bool = False
    reviewer: str = ""
    raw_marker: str = ""

    def to_dict(self) -> dict:
        # reviewer is redacted defensively (could be a free-form name/note).
        return {"approved": self.approved, "reviewer": redact_text(self.reviewer),
                "raw_marker": redact_text(self.raw_marker)}


def parse_approval(checklist_text: str) -> ApprovalRecord:
    """Read an approval checklist for the explicit marker + a named reviewer."""
    if not isinstance(checklist_text, str):
        return ApprovalRecord()
    marker_re = re.compile(rf"{APPROVAL_MARKER}\s*:\s*(true|yes)\b", re.IGNORECASE)
    m = marker_re.search(checklist_text)
    approved = bool(m)
    raw_marker = m.group(0) if m else ""
    rev = re.search(r"(?im)^\s*reviewer\s*:\s*(.+?)\s*$", checklist_text)
    reviewer = (rev.group(1).strip() if rev else "")
    # A placeholder like "<name>" or "TBD" is not a real reviewer.
    if reviewer.lower() in ("<name>", "tbd", "none", "n/a", ""):
        reviewer = ""
    return ApprovalRecord(approved=approved, reviewer=reviewer, raw_marker=raw_marker)


def validate_for_apply(proposal: RepairProposal,
                       approval: ApprovalRecord) -> RepairValidationResult:
    """Decide whether a proposal may be applied to an apply workspace.

    Fails closed: a still-invalid proposal, a missing approval marker, an empty
    reviewer, a non-apply-allowlisted or forbidden action, a forbidden target, or
    a secret-looking value all block apply.
    """
    errors: list[str] = []
    notes: list[str] = []

    if not isinstance(proposal, RepairProposal):
        return RepairValidationResult(valid=False, errors=["not_a_proposal"])

    # 1) The proposal must still be valid under the proposal validator.
    base = validate_proposal(proposal)
    if not base.valid:
        errors.append("proposal_revalidation_failed")
        errors.extend(f"proposal:{e}" for e in base.errors)

    # 2) Explicit human approval marker + a named reviewer.
    if approval is None or not approval.approved:
        errors.append("approval_marker_missing")
    if approval is None or not (approval.reviewer or "").strip():
        errors.append("reviewer_empty")

    # 3) Per-action apply restrictions (subset allowlist + protected targets).
    for idx, a in enumerate(proposal.actions):
        where = f"action[{idx}] id={a.id!r}"
        at = str(a.action_type)
        if at in ACTION_DENYLIST:
            errors.append(f"{where}: forbidden action_type {at!r}")
        elif at not in APPLY_ACTION_ALLOWLIST:
            errors.append(f"{where}: action_type {at!r} not in apply allowlist")
        if not _target_allowed(a.target):
            errors.append(f"{where}: target {a.target!r} outside allowed roots / protected")

    # 4) No secret-looking content anywhere (defense in depth; never echoed).
    try:
        blob = json.dumps(proposal.to_dict(), ensure_ascii=False, default=str)
    except Exception:  # noqa: BLE001
        blob = str(proposal.to_dict())
    if _contains_secret(blob):
        errors.append("proposal contains a secret-looking value")

    if any(a.action_type == "noop" for a in proposal.actions):
        notes.append("noop actions are recorded but materialize no change")

    return RepairValidationResult(valid=not errors, errors=errors, notes=notes)
