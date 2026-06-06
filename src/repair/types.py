"""Repair types — pure dataclasses, no external dependencies, no secrets.

These describe a *repair proposal*: a declarative, human-reviewable suggestion for
how to fix a failed eval. A proposal is NEVER applied, executed, or promoted by
this layer (see `specs/repair/repair_loop_contract.md`).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

RISK_LEVELS = ("low", "medium", "high")

FAILURE_TYPES = (
    "missing_artifact",
    "criterion_failed",
    "runtime_missing",
    "test_failed",
    "console_error",
    "unknown",
)


@dataclass
class FailureSignal:
    """One observation pulled from a failed run's artifacts (already redacted)."""

    source: str          # "score" | "summary" | "trace"
    kind: str            # e.g. "criterion_failed", "step_error", "fatal_console"
    detail: str = ""     # redacted, human-readable
    criterion: str = ""  # the failing criterion, if any

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FailureAnalysis:
    """The classified result of reading a failed run's artifacts."""

    run_ref: str
    failure_type: str            # one of FAILURE_TYPES
    unmet_criteria: list[str] = field(default_factory=list)
    signals: list[FailureSignal] = field(default_factory=list)
    summary: str = ""            # redacted
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "run_ref": self.run_ref,
            "failure_type": self.failure_type,
            "unmet_criteria": list(self.unmet_criteria),
            "signals": [s.to_dict() for s in self.signals],
            "summary": self.summary,
            "metadata": dict(self.metadata),
        }


@dataclass
class RepairAction:
    """One declarative, allowlisted repair step. Describes intent, not a command."""

    id: str
    action_type: str             # update_candidate | add_test | update_docs | update_eval | noop
    target: str                  # a path inside an allowed root
    reason: str = ""             # redacted
    risk_level: str = "low"
    requires_approval: bool = False
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    tests_to_run: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RepairProposal:
    """A declarative repair proposal. `applied` is ALWAYS False at this layer."""

    id: str
    failure_type: str
    actions: list[RepairAction] = field(default_factory=list)
    rationale: str = ""          # redacted
    marker: str = ""
    applied: bool = False        # invariant: never True here
    metadata: dict = field(default_factory=dict)

    @property
    def action_types(self) -> list[str]:
        return [a.action_type for a in self.actions]

    @property
    def targets(self) -> list[str]:
        return [a.target for a in self.actions]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "failure_type": self.failure_type,
            "actions": [a.to_dict() for a in self.actions],
            "rationale": self.rationale,
            "marker": self.marker,
            "applied": bool(self.applied),
            "metadata": dict(self.metadata),
        }


@dataclass
class RepairValidationResult:
    """Outcome of validating a proposal. `valid` only when `errors` is empty."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors), "notes": list(self.notes)}


@dataclass
class CandidateWorkspacePlan:
    """Record of the proposal workspace that was written (no target file touched)."""

    proposal_id: str
    workspace_dir: str
    files_written: list[str] = field(default_factory=list)
    applied: bool = False        # invariant: never True here

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "workspace_dir": self.workspace_dir,
            "files_written": list(self.files_written),
            "applied": bool(self.applied),
        }
