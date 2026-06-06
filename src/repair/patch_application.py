"""Patch application (v0) — materialize an approved proposal into an apply
workspace. NEVER touches a real repo file.

This writes *proposed* changes into an apply workspace under
`harnesses/candidates/_repair_applications/<apply_id>/`. It never overwrites the
proposal's target files, never promotes, and never runs arbitrary shell. The only
test commands it knows about are a FIXED allowlist (recorded; executed only when a
caller explicitly opts in, and even then only these exact commands).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.llm.redaction import redact_mapping, redact_text
from src.repair.apply_report import render_apply_report
from src.repair.types import RepairProposal

# Default base for apply workspaces (clearly namespaced; not an active candidate).
DEFAULT_APPLY_BASE = "harnesses/candidates/_repair_applications"

# FIXED, hardcoded test allowlist — NEVER derived from a proposal. These are the
# only commands repair_apply is ever allowed to run, and only on explicit opt-in.
ALLOWLISTED_TEST_COMMANDS = (
    "python scripts/validate_structure.py",
    "python scripts/validate_workflows.py",
    "python scripts/run_unit_tests.py",
    "python scripts/run_demo.py --demo vite_login_bug",
)


@dataclass
class ApplyManifest:
    """Record of an apply workspace (no target file modified)."""

    apply_id: str
    workspace_dir: str
    proposal_id: str
    approved_by: str = ""
    actions: list[dict] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    promoted: bool = False          # invariant: never promoted here
    stable_modified: bool = False   # invariant: never true here
    workspace_only: bool = True     # invariant: apply only ever touches a workspace

    def to_dict(self) -> dict:
        return redact_mapping({
            "apply_id": self.apply_id,
            "workspace_dir": self.workspace_dir,
            "proposal_id": self.proposal_id,
            "approved_by": self.approved_by,
            "actions": list(self.actions),
            "files_written": list(self.files_written),
            "test_commands": list(self.test_commands),
            "promoted": self.promoted,
            "stable_modified": self.stable_modified,
            "workspace_only": self.workspace_only,
        })


def proposal_from_dict(d: dict) -> RepairProposal:
    """Reconstruct a RepairProposal from a (render_json) proposal dict."""
    from src.repair.types import RepairAction
    pd = d.get("proposal", d)
    actions = [RepairAction(**a) for a in pd.get("actions", [])]
    return RepairProposal(
        id=pd.get("id", ""), failure_type=pd.get("failure_type", ""),
        actions=actions, rationale=pd.get("rationale", ""), marker=pd.get("marker", ""),
        applied=bool(pd.get("applied", False)), metadata=pd.get("metadata", {}))


def load_proposal_workspace(path: str | Path):
    """Load (proposal, analysis_dict, approval_text) from a proposal workspace."""
    ws = Path(path)
    proposal_doc = json.loads((ws / "repair_proposal.json").read_text(encoding="utf-8"))
    proposal = proposal_from_dict(proposal_doc)
    analysis = {}
    fa = ws / "failure_analysis.json"
    if fa.exists():
        analysis = json.loads(fa.read_text(encoding="utf-8"))
    approval_text = ""
    ac = ws / "approval_checklist.md"
    if ac.exists():
        approval_text = ac.read_text(encoding="utf-8")
    return proposal, analysis, approval_text


def _safe_name(target: str) -> str:
    """Turn a target path into a safe, traversal-free filename for the workspace."""
    t = (target or "change").strip().lstrip("./")
    t = t.replace("..", "_").replace("/", "__").replace("\\", "__")
    return t or "change"


# Per-action-type subfolder + a safe proposed-file extension.
_PROPOSED_LAYOUT = {
    "update_docs": ("docs", ".md"),
    "update_eval": ("evals", ".yaml"),
    "add_test": ("tests", ".py"),
    "update_candidate": ("candidate", ".patch_note.md"),
}


def _proposed_body(action) -> str:
    """A safe, redacted, human-readable *proposed change* note (NOT a live diff)."""
    return (
        f"# Proposed change (NOT APPLIED to the repo)\n\n"
        f"> APPROVED APPLICATION WORKSPACE ONLY — STABLE UNTOUCHED — NOT PROMOTED\n\n"
        f"- action id: {redact_text(action.id)}\n"
        f"- action_type: {redact_text(action.action_type)}\n"
        f"- intended target: `{redact_text(action.target)}`\n"
        f"- reason: {redact_text(action.reason)}\n"
        f"- risk: {action.risk_level} (approval required: "
        f"{'yes' if action.requires_approval else 'no'})\n"
        f"- tests to run: {', '.join(action.tests_to_run) or '-'}\n\n"
        f"This file is a *proposed* change living inside the apply workspace. It has\n"
        f"NOT been written to its intended target. A human must review and merge it\n"
        f"separately; merge and promotion are out of scope for this phase.\n"
    )


def apply_proposal(proposal: RepairProposal, approval, validation, *,
                   apply_id: str, base_dir: str | Path,
                   test_results: dict | None = None) -> ApplyManifest:
    """Materialize an approved proposal into an apply workspace.

    Writes `proposed_changes/...`, `apply_manifest.json`, `apply_report.md`, and
    `test_results.json`. Never overwrites a target file, never promotes.
    """
    workspace = Path(base_dir) / apply_id
    proposed = workspace / "proposed_changes"
    proposed.mkdir(parents=True, exist_ok=True)

    files: list[str] = []
    actions_record: list[dict] = []

    for a in proposal.actions:
        if a.action_type == "noop":
            actions_record.append({"id": a.id, "action_type": a.action_type,
                                   "target": a.target, "proposed_file": None,
                                   "materialized": False})
            continue
        subdir, ext = _PROPOSED_LAYOUT.get(a.action_type, ("misc", ".txt"))
        out_dir = proposed / subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{_safe_name(a.target)}{ext}"
        rel = f"proposed_changes/{subdir}/{fname}"
        (out_dir / fname).write_text(_proposed_body(a), encoding="utf-8")
        files.append(rel)
        actions_record.append({"id": a.id, "action_type": a.action_type,
                               "target": a.target, "proposed_file": rel,
                               "materialized": True})

    approved_by = getattr(approval, "reviewer", "") or ""
    manifest = ApplyManifest(
        apply_id=apply_id,
        workspace_dir=str(workspace),
        proposal_id=proposal.id,
        approved_by=approved_by,
        actions=actions_record,
        files_written=files,
        test_commands=list(ALLOWLISTED_TEST_COMMANDS),
        promoted=False,
        stable_modified=False,
    )

    # Write the manifest (redacted), the report, and the recorded test results.
    (workspace / "apply_manifest.json").write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    files.append("apply_manifest.json")

    results = test_results or {
        "executed": False,
        "note": "fixed allowlist recorded; not executed in this run",
        "commands": list(ALLOWLISTED_TEST_COMMANDS),
        "results": [],
    }
    (workspace / "test_results.json").write_text(
        json.dumps(redact_mapping(results), ensure_ascii=False, indent=2), encoding="utf-8")
    files.append("test_results.json")

    (workspace / "apply_report.md").write_text(
        render_apply_report(manifest, validation, results), encoding="utf-8")
    files.append("apply_report.md")

    (workspace / "README.md").write_text(_readme(apply_id, proposal.id), encoding="utf-8")
    files.append("README.md")

    manifest.files_written = files
    return manifest


def _readme(apply_id: str, proposal_id: str) -> str:
    return (
        f"# Apply workspace — `{apply_id}`\n\n"
        f"> APPROVED APPLICATION WORKSPACE ONLY — STABLE UNTOUCHED — NOT PROMOTED —\n"
        f"> HUMAN REVIEW STILL REQUIRED FOR MERGE/PROMOTION\n\n"
        f"This is an apply workspace for approved repair proposal `{proposal_id}`.\n"
        f"It contains *proposed* changes only, under `proposed_changes/`. **No repo\n"
        f"target file was modified, nothing was promoted, and no stable skill,\n"
        f"safety gate, or promotion policy was touched.** Merge and promotion are a\n"
        f"separate, human-driven phase (`specs/repair/approved_patch_application_contract.md`).\n"
    )
