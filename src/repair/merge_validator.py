"""Merge validation — gate an approved apply workspace for candidate-workspace merge.

This is the stricter gate that must pass before an apply workspace may be merged
into a new candidate merge workspace. It verifies the apply workspace structure,
its workspace-only invariants, an explicit human merge-approval marker + named
reviewer, and that no proposed change targets a protected path or carries a secret.
It NEVER merges anything; it only decides whether merge is allowed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.llm.redaction import redact_text
from src.repair.apply_validator import ApprovalRecord
from src.repair.proposal_validator import ACTION_DENYLIST, _target_allowed

# The merge-approval marker a human must place in merge_approval_checklist.md.
MERGE_APPROVAL_MARKER = "APPROVED_FOR_CANDIDATE_MERGE"

# Required files in an apply workspace before it can be merged.
REQUIRED_APPLY_FILES = ("apply_manifest.json", "apply_report.md", "test_results.json")
REQUIRED_APPLY_DIRS = ("proposed_changes",)


@dataclass
class MergeValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    reviewer: str = ""
    manifest: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors),
                "notes": list(self.notes), "reviewer": redact_text(self.reviewer)}


def parse_merge_approval(checklist_text: str) -> ApprovalRecord:
    """Read a merge approval checklist for the marker + a named reviewer."""
    if not isinstance(checklist_text, str):
        return ApprovalRecord()
    m = re.search(rf"{MERGE_APPROVAL_MARKER}\s*:\s*(true|yes)\b", checklist_text, re.IGNORECASE)
    raw = m.group(0) if m else ""
    rev = re.search(r"(?im)^\s*reviewer\s*:\s*(.+?)\s*$", checklist_text)
    reviewer = rev.group(1).strip() if rev else ""
    if reviewer.lower() in ("<name>", "tbd", "todo", "unknown", "none", "n/a", ""):
        reviewer = ""
    return ApprovalRecord(approved=bool(m), reviewer=reviewer, raw_marker=raw)


def _contains_secret(text: str) -> bool:
    return redact_text(text) != text


def load_apply_workspace(path: str | Path):
    """Return (manifest_dict, merge_approval_text) for an apply workspace."""
    ws = Path(path)
    manifest = {}
    mf = ws / "apply_manifest.json"
    if mf.exists():
        try:
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    approval_text = ""
    ac = ws / "merge_approval_checklist.md"
    if ac.exists():
        approval_text = ac.read_text(encoding="utf-8")
    return manifest, approval_text


def validate_merge(apply_workspace: str | Path, *, reviewer_override: str = "") -> MergeValidationResult:
    """Decide whether an apply workspace may be merged into a candidate workspace.

    Fail closed: a missing structure, a non-workspace-only manifest, a missing
    merge-approval marker, an empty reviewer, a forbidden/denylisted action, or a
    secret-looking proposed change all block merge.
    """
    ws = Path(apply_workspace)
    errors: list[str] = []
    notes: list[str] = []

    if not ws.exists() or not ws.is_dir():
        return MergeValidationResult(valid=False, errors=["apply_workspace_missing"])

    # 1) Structure.
    for f in REQUIRED_APPLY_FILES:
        if not (ws / f).exists():
            errors.append(f"missing apply file: {f}")
    for d in REQUIRED_APPLY_DIRS:
        if not (ws / d).is_dir():
            errors.append(f"missing apply dir: {d}/")

    manifest, approval_text = load_apply_workspace(ws)

    # 2) Manifest invariants — apply must have been workspace-only, not promoted.
    if manifest.get("promoted") is not False:
        errors.append("apply_manifest.promoted is not false")
    if manifest.get("stable_modified") is not False:
        errors.append("apply_manifest.stable_modified is not false")
    if manifest.get("workspace_only") is not True:
        errors.append("apply_manifest.workspace_only is not true")

    # 3) Human merge approval + named reviewer.
    approval = parse_merge_approval(approval_text)
    if not approval.approved:
        errors.append("merge_approval_marker_missing")
    reviewer = (reviewer_override or approval.reviewer or "").strip()
    if reviewer.lower() in ("", "<name>", "tbd", "todo", "unknown", "none", "n/a"):
        errors.append("reviewer_empty")
        reviewer = ""

    # 4) Per-action protected-target + denylist checks (from the manifest actions).
    for idx, a in enumerate(manifest.get("actions", []) or []):
        at = str(a.get("action_type", ""))
        target = str(a.get("target", ""))
        if at in ACTION_DENYLIST:
            errors.append(f"action[{idx}]: forbidden action_type {at!r}")
        if target and not _target_allowed(target):
            errors.append(f"action[{idx}]: target {target!r} outside allowed roots / protected")

    # 5) No secret-looking content in any proposed_changes file (never echoed).
    proposed = ws / "proposed_changes"
    if proposed.is_dir():
        for p in proposed.rglob("*"):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if _contains_secret(text):
                errors.append(f"proposed change contains a secret-looking value: "
                              f"{p.relative_to(ws)}")

    return MergeValidationResult(valid=not errors, errors=errors, notes=notes,
                                 reviewer=reviewer, manifest=manifest)
