"""Repair package — Auto Repair Loop v0: PROPOSAL ONLY.

Reads a failed run, classifies the failure, and produces a declarative repair
*proposal* in a candidate workspace. It NEVER applies a patch, runs a test,
modifies a stable skill, or promotes anything. See
`specs/repair/repair_loop_contract.md`.
"""
from src.repair.types import (
    FailureSignal,
    FailureAnalysis,
    RepairAction,
    RepairProposal,
    RepairValidationResult,
    CandidateWorkspacePlan,
    RISK_LEVELS,
    FAILURE_TYPES,
)
from src.repair.failure_analyzer import analyze_failure
from src.repair.fake_repair_planner import (
    FakeRepairPlanner,
    MARKER_MISSING_ARTIFACT,
    MARKER_TEST_FAILED,
    MARKER_CONSOLE_ERROR,
)
from src.repair.proposal_validator import (
    validate_proposal,
    ACTION_ALLOWLIST,
    ACTION_DENYLIST,
    ALLOWED_TARGET_ROOTS,
    FORBIDDEN_TARGET_PREFIXES,
)
from src.repair.proposal_renderer import render_json, render_markdown, BANNER
from src.repair.candidate_workspace import create_workspace, DEFAULT_BASE
from src.repair.apply_validator import (
    validate_for_apply,
    parse_approval,
    ApprovalRecord,
    APPROVAL_MARKER,
    APPLY_ACTION_ALLOWLIST,
)
from src.repair.patch_application import (
    apply_proposal,
    proposal_from_dict,
    load_proposal_workspace,
    ApplyManifest,
    ALLOWLISTED_TEST_COMMANDS,
    DEFAULT_APPLY_BASE,
)
from src.repair.apply_report import render_apply_report, BANNER_LINES
from src.repair.merge_validator import (
    validate_merge,
    parse_merge_approval,
    MergeValidationResult,
    MERGE_APPROVAL_MARKER,
    load_apply_workspace,
)
from src.repair.candidate_merge import (
    create_merge_workspace,
    MergeManifest,
    DEFAULT_MERGE_BASE,
    MERGE_TEST_COMMANDS,
    TARGETED_TEST_COMMANDS,
    REGRESSION_TEST_COMMANDS,
)
from src.repair.merge_report import render_merge_report, BANNER_LINES as MERGE_BANNER_LINES
from src.repair.staging_validator import (
    validate_staging,
    parse_staging_approval,
    StagingValidationResult,
    STAGING_APPROVAL_MARKER,
    load_merge_workspace,
)
from src.repair.staging_promotion import (
    create_staging_workspace,
    StagingManifest,
    DEFAULT_STAGING_BASE,
    STAGING_TEST_COMMANDS,
    TARGETED_TEST_COMMANDS as STAGING_TARGETED_TEST_COMMANDS,
    REGRESSION_TEST_COMMANDS as STAGING_REGRESSION_TEST_COMMANDS,
)
from src.repair.staging_report import render_staging_report

__all__ = [
    "FailureSignal",
    "FailureAnalysis",
    "RepairAction",
    "RepairProposal",
    "RepairValidationResult",
    "CandidateWorkspacePlan",
    "RISK_LEVELS",
    "FAILURE_TYPES",
    "analyze_failure",
    "FakeRepairPlanner",
    "MARKER_MISSING_ARTIFACT",
    "MARKER_TEST_FAILED",
    "MARKER_CONSOLE_ERROR",
    "validate_proposal",
    "ACTION_ALLOWLIST",
    "ACTION_DENYLIST",
    "ALLOWED_TARGET_ROOTS",
    "FORBIDDEN_TARGET_PREFIXES",
    "render_json",
    "render_markdown",
    "BANNER",
    "create_workspace",
    "DEFAULT_BASE",
    "validate_for_apply",
    "parse_approval",
    "ApprovalRecord",
    "APPROVAL_MARKER",
    "APPLY_ACTION_ALLOWLIST",
    "apply_proposal",
    "proposal_from_dict",
    "load_proposal_workspace",
    "ApplyManifest",
    "ALLOWLISTED_TEST_COMMANDS",
    "DEFAULT_APPLY_BASE",
    "render_apply_report",
    "BANNER_LINES",
    "validate_merge",
    "parse_merge_approval",
    "MergeValidationResult",
    "MERGE_APPROVAL_MARKER",
    "load_apply_workspace",
    "create_merge_workspace",
    "MergeManifest",
    "DEFAULT_MERGE_BASE",
    "MERGE_TEST_COMMANDS",
    "TARGETED_TEST_COMMANDS",
    "REGRESSION_TEST_COMMANDS",
    "render_merge_report",
    "MERGE_BANNER_LINES",
    "validate_staging",
    "parse_staging_approval",
    "StagingValidationResult",
    "STAGING_APPROVAL_MARKER",
    "load_merge_workspace",
    "create_staging_workspace",
    "StagingManifest",
    "DEFAULT_STAGING_BASE",
    "STAGING_TEST_COMMANDS",
    "STAGING_TARGETED_TEST_COMMANDS",
    "STAGING_REGRESSION_TEST_COMMANDS",
    "render_staging_report",
]
