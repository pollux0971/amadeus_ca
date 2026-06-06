"""Candidate merge (v0) — merge an approved apply workspace into a NEW candidate
merge workspace. NEVER touches a repo target, an active candidate, or stable.

This copies an apply workspace's `proposed_changes/` into a fresh candidate merge
workspace under `harnesses/candidates/_repair_merges/<merge_id>/`, and writes a
merge manifest, report, rollback plan, and promotion review package. It never
overwrites a real file, never modifies an active candidate or stable, and never
promotes. Test commands are a FIXED allowlist (never from the apply workspace).
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from src.llm.redaction import redact_mapping, redact_text
from src.repair.merge_report import render_merge_report

# Default base for candidate merge workspaces (namespaced; not an active candidate).
DEFAULT_MERGE_BASE = "harnesses/candidates/_repair_merges"

# FIXED, hardcoded test allowlist — NEVER derived from an apply workspace.
TARGETED_TEST_COMMANDS = (
    "python scripts/validate_structure.py",
    "python scripts/validate_workflows.py",
    "python scripts/run_unit_tests.py",
)
REGRESSION_TEST_COMMANDS = (
    "python scripts/run_demo.py --demo vite_login_bug",
    "python scripts/run_eval.py --task evals/repair/fake_approved_patch_application.yaml",
    "python scripts/run_eval.py --task evals/repair/fake_repair_proposal_only.yaml",
)
MERGE_TEST_COMMANDS = TARGETED_TEST_COMMANDS + REGRESSION_TEST_COMMANDS


@dataclass
class MergeManifest:
    merge_id: str
    workspace_dir: str
    source_apply_workspace: str
    reviewer: str = ""
    merged_files: list[str] = field(default_factory=list)
    targeted_tests: list[str] = field(default_factory=list)
    regression_tests: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    merged_to_candidate_workspace: bool = True
    stable_modified: bool = False
    promoted: bool = False
    rollback_available: bool = True

    def to_dict(self) -> dict:
        return redact_mapping({
            "merge_id": self.merge_id,
            "workspace_dir": self.workspace_dir,
            "source_apply_workspace": self.source_apply_workspace,
            "reviewer": self.reviewer,
            "merged_files": list(self.merged_files),
            "targeted_tests": list(self.targeted_tests),
            "regression_tests": list(self.regression_tests),
            "files_written": list(self.files_written),
            "merged_to_candidate_workspace": self.merged_to_candidate_workspace,
            "stable_modified": self.stable_modified,
            "promoted": self.promoted,
            "rollback_available": self.rollback_available,
        })


def _rollback_plan(merge_id: str, workspace_dir: str, source: str) -> str:
    return (
        f"# Rollback plan — merge `{merge_id}`\n\n"
        f"> CANDIDATE WORKSPACE MERGE ONLY — STABLE UNTOUCHED — NOT PROMOTED\n\n"
        "This merge created a NEW candidate merge workspace and copied proposed\n"
        "changes into it. **No repo target file, active candidate, stable skill,\n"
        "safety gate, or promotion policy was modified.** Rolling back is therefore\n"
        "trivial and fully reversible:\n\n"
        f"1. Delete the merge workspace directory: `{redact_text(workspace_dir)}`.\n"
        "2. Nothing else needs to change — the live tree was never touched.\n\n"
        f"Source apply workspace (unchanged): `{redact_text(source)}`.\n\n"
        "Because no promotion or stable change occurred, there is no deployed state\n"
        "to revert. A future staging/stable promotion phase must define its own,\n"
        "stronger rollback before changing any active/stable artifact.\n"
    )


def _promotion_review_package(merge_id: str, manifest: MergeManifest) -> str:
    lines = [
        f"# Promotion review package — merge `{merge_id}`",
        "",
        "> CANDIDATE WORKSPACE MERGE ONLY — STABLE UNTOUCHED — NOT PROMOTED —",
        "> HUMAN REVIEW REQUIRED BEFORE STAGING/STABLE",
        "",
        "A human reviewer uses this package to decide whether to take the merged",
        "candidate forward. **Nothing here promotes anything.**",
        "",
        f"- merge id: `{merge_id}`",
        f"- reviewer: {redact_text(manifest.reviewer) or '(none)'}",
        f"- source apply workspace: `{redact_text(manifest.source_apply_workspace)}`",
        f"- merged files: {len(manifest.merged_files)}",
        f"- rollback available: {manifest.rollback_available}",
        "",
        "## Pre-promotion checklist (human must clear)",
        "- [ ] Reviewed every merged change in `merged_changes/`.",
        "- [ ] Targeted tests pass (see `test_results.json` / run the fixed allowlist).",
        "- [ ] Regression suite passes.",
        "- [ ] No stable skill / safety gate / promotion policy is affected.",
        "- [ ] `rollback_plan.md` is sufficient.",
        "- [ ] Promotion (if any) follows `specs/harness/promotion_policy.md`.",
        "",
        "## Fixed test allowlist",
        "- targeted:",
        *[f"  - `{c}`" for c in manifest.targeted_tests],
        "- regression:",
        *[f"  - `{c}`" for c in manifest.regression_tests],
        "",
        "> Staging/stable promotion is a separate, human-driven phase. This package",
        "> is input to that decision, not the decision itself.",
    ]
    return "\n".join(lines) + "\n"


def _readme(merge_id: str, source: str) -> str:
    return (
        f"# Candidate merge workspace — `{merge_id}`\n\n"
        f"> CANDIDATE WORKSPACE MERGE ONLY — STABLE UNTOUCHED — NOT PROMOTED —\n"
        f"> HUMAN REVIEW REQUIRED BEFORE STAGING/STABLE\n\n"
        f"This is a candidate merge workspace built from approved apply workspace\n"
        f"`{redact_text(source)}`. It holds the merged proposed changes under\n"
        f"`merged_changes/`, a `merge_manifest.json`, a `merge_report.md`, a\n"
        f"`rollback_plan.md`, a `promotion_review_package.md`, and `test_results.json`.\n\n"
        f"**No repo target file, active candidate, stable skill, safety gate, or\n"
        f"promotion policy was modified, and nothing was promoted.** Staging/stable\n"
        f"promotion is a separate, human-driven phase\n"
        f"(`specs/repair/candidate_merge_contract.md`).\n"
    )


def create_merge_workspace(apply_workspace: str | Path, validation, *, merge_id: str,
                           base_dir: str | Path, reviewer: str,
                           test_results: dict | None = None) -> MergeManifest:
    """Build a candidate merge workspace from an apply workspace. No repo target,
    active candidate, or stable is touched."""
    apply_ws = Path(apply_workspace)
    workspace = Path(base_dir) / merge_id
    merged = workspace / "merged_changes"
    merged.mkdir(parents=True, exist_ok=True)

    merged_files: list[str] = []
    src_proposed = apply_ws / "proposed_changes"
    if src_proposed.is_dir():
        for p in sorted(src_proposed.rglob("*")):
            if p.is_file():
                rel = p.relative_to(src_proposed)
                dest = merged / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, dest)
                merged_files.append(f"merged_changes/{rel}")

    manifest = MergeManifest(
        merge_id=merge_id,
        workspace_dir=str(workspace),
        source_apply_workspace=str(apply_ws),
        reviewer=reviewer,
        merged_files=merged_files,
        targeted_tests=list(TARGETED_TEST_COMMANDS),
        regression_tests=list(REGRESSION_TEST_COMMANDS),
        merged_to_candidate_workspace=True,
        stable_modified=False,
        promoted=False,
        rollback_available=True,
    )

    files = list(merged_files)

    def _write(name: str, text: str) -> None:
        (workspace / name).write_text(text, encoding="utf-8")
        files.append(name)

    _write("merge_manifest.json", json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
    results = test_results or {
        "executed": False, "note": "fixed allowlist recorded; not executed",
        "commands": list(MERGE_TEST_COMMANDS), "results": []}
    _write("test_results.json", json.dumps(redact_mapping(results), ensure_ascii=False, indent=2))
    _write("merge_report.md", render_merge_report(manifest.to_dict(), validation, results))
    _write("rollback_plan.md", _rollback_plan(merge_id, str(workspace), str(apply_ws)))
    _write("promotion_review_package.md", _promotion_review_package(merge_id, manifest))
    _write("README.md", _readme(merge_id, str(apply_ws)))

    manifest.files_written = files
    # Re-write the manifest now that files_written is complete.
    (workspace / "merge_manifest.json").write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
