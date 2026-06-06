"""Staging validation — gate an approved candidate merge workspace for staging promotion.

This is the stricter gate that must pass before a candidate merge workspace may be
promoted into a staging promotion workspace. It verifies the merge workspace
structure, its candidate-workspace-only invariants, an explicit human staging
approval marker + named reviewer, that the rollback plan and promotion review
package exist and are non-empty, and that no merged change targets a protected path
or carries a secret. It NEVER promotes anything; it only decides whether staging is
allowed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.llm.redaction import redact_text
from src.repair.apply_validator import ApprovalRecord
from src.repair.proposal_validator import ACTION_DENYLIST, _target_allowed

# The staging-approval marker a human must place in staging_approval_checklist.md.
STAGING_APPROVAL_MARKER = "APPROVED_FOR_STAGING_PROMOTION"

# Required files in a candidate merge workspace before it can be staged.
REQUIRED_MERGE_FILES = (
    "merge_manifest.json", "merge_report.md", "rollback_plan.md",
    "promotion_review_package.md", "test_results.json",
)
REQUIRED_MERGE_DIRS = ("merged_changes",)


@dataclass
class StagingValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    reviewer: str = ""
    manifest: dict = field(default_factory=dict)
    rollback_present: bool = False

    def to_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors),
                "notes": list(self.notes), "reviewer": redact_text(self.reviewer),
                "rollback_present": self.rollback_present}


def parse_staging_approval(checklist_text: str) -> ApprovalRecord:
    """Read a staging approval checklist for the marker + a named reviewer."""
    if not isinstance(checklist_text, str):
        return ApprovalRecord()
    m = re.search(rf"{STAGING_APPROVAL_MARKER}\s*:\s*(true|yes)\b", checklist_text, re.IGNORECASE)
    raw = m.group(0) if m else ""
    rev = re.search(r"(?im)^\s*reviewer\s*:\s*(.+?)\s*$", checklist_text)
    reviewer = rev.group(1).strip() if rev else ""
    if reviewer.lower() in ("<name>", "tbd", "todo", "unknown", "none", "n/a", ""):
        reviewer = ""
    return ApprovalRecord(approved=bool(m), reviewer=reviewer, raw_marker=raw)


def _contains_secret(text: str) -> bool:
    return redact_text(text) != text


def load_merge_workspace(path: str | Path):
    """Return (manifest_dict, staging_approval_text) for a candidate merge workspace."""
    ws = Path(path)
    manifest = {}
    mf = ws / "merge_manifest.json"
    if mf.exists():
        try:
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    approval_text = ""
    ac = ws / "staging_approval_checklist.md"
    if ac.exists():
        approval_text = ac.read_text(encoding="utf-8")
    return manifest, approval_text


def _non_empty_file(path: Path) -> bool:
    try:
        return path.is_file() and bool(path.read_text(encoding="utf-8").strip())
    except (OSError, UnicodeDecodeError):
        return False


def validate_staging(merge_workspace: str | Path, *, reviewer_override: str = "") -> StagingValidationResult:
    """Decide whether a candidate merge workspace may be promoted to staging.

    Fail closed: a missing structure, a non-candidate-workspace-only manifest, a
    missing staging-approval marker, an empty reviewer, a missing/empty rollback
    plan or promotion review package, a forbidden/denylisted action, or a
    secret-looking merged change all block staging.
    """
    ws = Path(merge_workspace)
    errors: list[str] = []
    notes: list[str] = []

    if not ws.exists() or not ws.is_dir():
        return StagingValidationResult(valid=False, errors=["merge_workspace_missing"])

    # 1) Structure.
    for f in REQUIRED_MERGE_FILES:
        if not (ws / f).exists():
            errors.append(f"missing merge file: {f}")
    for d in REQUIRED_MERGE_DIRS:
        if not (ws / d).is_dir():
            errors.append(f"missing merge dir: {d}/")

    manifest, approval_text = load_merge_workspace(ws)

    # 2) Manifest invariants — merge must have been candidate-workspace-only.
    if manifest.get("merged_to_candidate_workspace") is not True:
        errors.append("merge_manifest.merged_to_candidate_workspace is not true")
    if manifest.get("stable_modified") is not False:
        errors.append("merge_manifest.stable_modified is not false")
    if manifest.get("promoted") is not False:
        errors.append("merge_manifest.promoted is not false")
    if manifest.get("rollback_available") is not True:
        errors.append("merge_manifest.rollback_available is not true")

    # 3) Human staging approval + named reviewer.
    approval = parse_staging_approval(approval_text)
    if not approval.approved:
        errors.append("staging_approval_marker_missing")
    reviewer = (reviewer_override or approval.reviewer or "").strip()
    if reviewer.lower() in ("", "<name>", "tbd", "todo", "unknown", "none", "n/a"):
        errors.append("reviewer_empty")
        reviewer = ""

    # 4) Rollback plan + promotion review package present and non-empty.
    rollback_present = _non_empty_file(ws / "rollback_plan.md")
    if not rollback_present:
        errors.append("rollback_plan.md missing or empty")
    if not _non_empty_file(ws / "promotion_review_package.md"):
        errors.append("promotion_review_package.md missing or empty")

    # 5) Per-action protected-target + denylist checks (from the manifest actions).
    for idx, a in enumerate(manifest.get("actions", []) or []):
        at = str(a.get("action_type", ""))
        target = str(a.get("target", ""))
        if at in ACTION_DENYLIST:
            errors.append(f"action[{idx}]: forbidden action_type {at!r}")
        if target and not _target_allowed(target):
            errors.append(f"action[{idx}]: target {target!r} outside allowed roots / protected")

    # 6) No secret-looking content in any merged_changes file (never echoed).
    merged = ws / "merged_changes"
    if merged.is_dir():
        for p in merged.rglob("*"):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if _contains_secret(text):
                errors.append(f"merged change contains a secret-looking value: "
                              f"{p.relative_to(ws)}")

    return StagingValidationResult(valid=not errors, errors=errors, notes=notes,
                                   reviewer=reviewer, manifest=manifest,
                                   rollback_present=rollback_present)
