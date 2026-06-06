"""Staging promotion (v0) — promote an approved candidate merge workspace into a
STAGING workspace. NEVER touches a repo target, an active candidate, or stable.

This copies a candidate merge workspace's `merged_changes/` into a staging
promotion workspace under `harnesses/candidates/_staging_promotions/<staging_id>/`,
and writes a staging manifest, report, rollback verification, regression results,
and a stable-promotion checklist. It never overwrites a real file, never modifies
an active candidate or stable, and never stable-promotes. Test commands are a FIXED
allowlist (never from the merge workspace).
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from src.llm.redaction import redact_mapping, redact_text
from src.repair.staging_report import render_staging_report

# Default base for staging promotion workspaces (namespaced; not an active candidate).
DEFAULT_STAGING_BASE = "harnesses/candidates/_staging_promotions"

# FIXED, hardcoded test allowlist — NEVER derived from a merge workspace.
TARGETED_TEST_COMMANDS = (
    "python scripts/validate_structure.py",
    "python scripts/validate_workflows.py",
    "python scripts/run_unit_tests.py",
)
REGRESSION_TEST_COMMANDS = (
    "python scripts/run_demo.py --demo vite_login_bug",
    "python scripts/run_eval.py --task evals/repair/fake_candidate_merge.yaml",
    "python scripts/run_eval.py --task evals/repair/fake_approved_patch_application.yaml",
    "python scripts/run_eval.py --task evals/repair/fake_repair_proposal_only.yaml",
    "python scripts/run_eval.py --task evals/planner/fake_full_browser_plan_execution.yaml",
)
STAGING_TEST_COMMANDS = TARGETED_TEST_COMMANDS + REGRESSION_TEST_COMMANDS


@dataclass
class StagingManifest:
    staging_id: str
    workspace_dir: str
    source_merge_workspace: str
    reviewer: str = ""
    staged_files: list[str] = field(default_factory=list)
    targeted_tests: list[str] = field(default_factory=list)
    regression_tests: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    staged: bool = True
    stable_modified: bool = False
    stable_promoted: bool = False
    active_candidate_modified: bool = False
    rollback_verified: bool = False

    def to_dict(self) -> dict:
        return redact_mapping({
            "staging_id": self.staging_id,
            "workspace_dir": self.workspace_dir,
            "source_merge_workspace": self.source_merge_workspace,
            "reviewer": self.reviewer,
            "staged_files": list(self.staged_files),
            "targeted_tests": list(self.targeted_tests),
            "regression_tests": list(self.regression_tests),
            "files_written": list(self.files_written),
            "staged": self.staged,
            "stable_modified": self.stable_modified,
            "stable_promoted": self.stable_promoted,
            "active_candidate_modified": self.active_candidate_modified,
            "rollback_verified": self.rollback_verified,
        })


def _rollback_verification(staging_id: str, workspace_dir: str, source: str,
                           rollback_present: bool) -> str:
    status = "VERIFIED" if rollback_present else "NEEDS REVIEW"
    return (
        f"# Rollback verification — staging `{staging_id}`\n\n"
        f"> STAGING WORKSPACE ONLY — STABLE UNTOUCHED — NOT STABLE PROMOTED\n\n"
        f"- rollback status: **{status}**\n"
        f"- source merge workspace (unchanged): `{redact_text(source)}`\n\n"
        "The source candidate merge workspace shipped a `rollback_plan.md`. This\n"
        "staging step copied its merged changes into a staging workspace only —\n"
        "**no repo target file, active candidate, stable skill, safety gate, or\n"
        "promotion policy was modified.** Rolling back the staging step is trivial\n"
        "and fully reversible:\n\n"
        f"1. Delete the staging workspace directory: `{redact_text(workspace_dir)}`.\n"
        "2. The source merge workspace and the live tree are unchanged.\n\n"
        "Because no stable promotion occurred, there is no deployed state to revert.\n"
        "A future stable-promotion phase must define its own, stronger rollback and\n"
        "have it verified before changing any stable artifact.\n"
    )


def _stable_promotion_checklist(staging_id: str, manifest: StagingManifest) -> str:
    lines = [
        f"# Stable promotion checklist — staging `{staging_id}`",
        "",
        "> STAGING WORKSPACE ONLY — STABLE UNTOUCHED — NOT STABLE PROMOTED —",
        "> HUMAN REVIEW REQUIRED BEFORE STABLE — PROMOTION POLICY STILL REQUIRED",
        "",
        "A human reviewer uses this checklist to decide whether to take the staged",
        "candidate toward stable. **Nothing here promotes anything.**",
        "",
        f"- staging id: `{staging_id}`",
        f"- reviewer: {redact_text(manifest.reviewer) or '(none)'}",
        f"- source merge workspace: `{redact_text(manifest.source_merge_workspace)}`",
        f"- staged files: {len(manifest.staged_files)}",
        f"- rollback verified: {manifest.rollback_verified}",
        "",
        "## Pre-stable-promotion checklist (human must clear)",
        "- [ ] Reviewed every staged change in `staged_changes/`.",
        "- [ ] Targeted tests pass (see `regression_results.json` / run the fixed allowlist).",
        "- [ ] Full regression suite passes.",
        "- [ ] Rollback verification is sufficient (`rollback_verification.md`).",
        "- [ ] No stable skill / safety gate / promotion policy is affected.",
        "- [ ] A human shell-execution review signed off (per the promotion policy).",
        "- [ ] Stable promotion follows `specs/harness/promotion_policy.md`.",
        "",
        "## Fixed test allowlist",
        "- targeted:",
        *[f"  - `{c}`" for c in manifest.targeted_tests],
        "- regression:",
        *[f"  - `{c}`" for c in manifest.regression_tests],
        "",
        "> Stable promotion is a separate, human-driven phase. This checklist is input",
        "> to that decision, not the decision itself.",
    ]
    return "\n".join(lines) + "\n"


def _readme(staging_id: str, source: str) -> str:
    return (
        f"# Staging promotion workspace — `{staging_id}`\n\n"
        f"> STAGING WORKSPACE ONLY — STABLE UNTOUCHED — NOT STABLE PROMOTED —\n"
        f"> HUMAN REVIEW REQUIRED BEFORE STABLE — PROMOTION POLICY STILL REQUIRED\n\n"
        f"This is a staging promotion workspace built from approved candidate merge\n"
        f"workspace `{redact_text(source)}`. It holds the staged changes under\n"
        f"`staged_changes/`, a `staging_manifest.json`, a `staging_report.md`, a\n"
        f"`rollback_verification.md`, a `regression_results.json`, and a\n"
        f"`stable_promotion_checklist.md`.\n\n"
        f"**No repo target file, active candidate, stable skill, safety gate, or\n"
        f"promotion policy was modified, and nothing was stable-promoted.** Stable\n"
        f"promotion is a separate, human-driven phase\n"
        f"(`specs/repair/staging_promotion_contract.md`).\n"
    )


def create_staging_workspace(merge_workspace: str | Path, validation, *, staging_id: str,
                             base_dir: str | Path, reviewer: str,
                             regression_results: dict | None = None) -> StagingManifest:
    """Build a staging promotion workspace from a candidate merge workspace. No repo
    target, active candidate, or stable is touched."""
    merge_ws = Path(merge_workspace)
    workspace = Path(base_dir) / staging_id
    staged = workspace / "staged_changes"
    staged.mkdir(parents=True, exist_ok=True)

    staged_files: list[str] = []
    src_merged = merge_ws / "merged_changes"
    if src_merged.is_dir():
        for p in sorted(src_merged.rglob("*")):
            if p.is_file():
                rel = p.relative_to(src_merged)
                dest = staged / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, dest)
                staged_files.append(f"staged_changes/{rel}")

    rollback_verified = bool(getattr(validation, "rollback_present", False))
    manifest = StagingManifest(
        staging_id=staging_id,
        workspace_dir=str(workspace),
        source_merge_workspace=str(merge_ws),
        reviewer=reviewer,
        staged_files=staged_files,
        targeted_tests=list(TARGETED_TEST_COMMANDS),
        regression_tests=list(REGRESSION_TEST_COMMANDS),
        staged=True,
        stable_modified=False,
        stable_promoted=False,
        active_candidate_modified=False,
        rollback_verified=rollback_verified,
    )

    files = list(staged_files)

    def _write(name: str, text: str) -> None:
        (workspace / name).write_text(text, encoding="utf-8")
        files.append(name)

    _write("staging_manifest.json", json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
    results = regression_results or {
        "executed": False, "note": "fixed allowlist recorded; not executed",
        "commands": list(STAGING_TEST_COMMANDS), "results": []}
    _write("regression_results.json", json.dumps(redact_mapping(results), ensure_ascii=False, indent=2))
    _write("staging_report.md", render_staging_report(manifest.to_dict(), validation, results))
    _write("rollback_verification.md",
           _rollback_verification(staging_id, str(workspace), str(merge_ws), rollback_verified))
    _write("stable_promotion_checklist.md", _stable_promotion_checklist(staging_id, manifest))
    _write("README.md", _readme(staging_id, str(merge_ws)))

    manifest.files_written = files
    (workspace / "staging_manifest.json").write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
