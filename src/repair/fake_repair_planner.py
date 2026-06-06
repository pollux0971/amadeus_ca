"""FakeRepairPlanner — deterministic, offline repair-proposal generator.

Given a `FailureAnalysis`, it produces a declarative `RepairProposal` using ONLY
the offline `FakeLLMProvider`. It:

- makes no network call, reads no env var, makes no real API call;
- never emits a raw shell command or a destructive action;
- only proposes allowlisted action types against allowed target roots;
- never marks a proposal as applied (the proposal is a suggestion only).

Markers (also detected from the analysis failure_type):
  - FAKE_REPAIR_MISSING_ARTIFACT
  - FAKE_REPAIR_TEST_FAILED
  - FAKE_REPAIR_CONSOLE_ERROR
  - (none) -> a noop proposal
"""
from __future__ import annotations

from src.llm.fake_provider import FakeLLMProvider
from src.llm.redaction import redact_text
from src.llm.types import LLMMessage, LLMRequest
from src.repair.types import RepairAction, RepairProposal

MARKER_MISSING_ARTIFACT = "FAKE_REPAIR_MISSING_ARTIFACT"
MARKER_TEST_FAILED = "FAKE_REPAIR_TEST_FAILED"
MARKER_CONSOLE_ERROR = "FAKE_REPAIR_CONSOLE_ERROR"

_KNOWN_MARKERS = (MARKER_MISSING_ARTIFACT, MARKER_TEST_FAILED, MARKER_CONSOLE_ERROR)

# Map an analyzer failure_type to a marker so the planner is usable without an
# explicit marker (still deterministic).
_FAILURE_TYPE_MARKER = {
    "missing_artifact": MARKER_MISSING_ARTIFACT,
    "test_failed": MARKER_TEST_FAILED,
    "console_error": MARKER_CONSOLE_ERROR,
}


def _proposal_id(marker: str) -> str:
    stem = (marker or "noop").lower().replace("fake_repair_", "").strip("_") or "noop"
    return f"repair_{stem}"


def _missing_artifact_proposal(analysis) -> RepairProposal:
    pid = _proposal_id(MARKER_MISSING_ARTIFACT)
    return RepairProposal(
        id=pid, failure_type="missing_artifact", marker=MARKER_MISSING_ARTIFACT,
        rationale="A required artifact was not produced; propose ensuring the eval "
                  "asserts the artifact and adding a regression test (PROPOSAL ONLY).",
        actions=[
            RepairAction(
                id="a1", action_type="update_eval",
                target="evals/<eval-that-failed>.yaml",
                reason="Ensure the eval declares/checks the missing artifact output.",
                risk_level="low", requires_approval=False,
                allowed_files=["evals/"], forbidden_files=["skills/", "src/agents/safety_gate/"],
                tests_to_run=["tests/unit/"]),
            RepairAction(
                id="a2", action_type="add_test",
                target="tests/unit/test_artifact_present.py",
                reason="Add a regression test asserting the artifact reference exists.",
                risk_level="low", requires_approval=False,
                allowed_files=["tests/"], forbidden_files=["skills/"],
                tests_to_run=["tests/unit/test_artifact_present.py"]),
        ],
        metadata={"unmet": list(analysis.unmet_criteria)},
    )


def _test_failed_proposal(analysis) -> RepairProposal:
    pid = _proposal_id(MARKER_TEST_FAILED)
    return RepairProposal(
        id=pid, failure_type="test_failed", marker=MARKER_TEST_FAILED,
        rationale="Tests failed after the change; propose a candidate-side fix and a "
                  "regression test. No patch is applied (PROPOSAL ONLY).",
        actions=[
            RepairAction(
                id="a1", action_type="update_candidate",
                target="harnesses/candidates/<candidate-id>/",
                reason="Propose a minimal fix in the candidate so its tests pass.",
                risk_level="medium", requires_approval=False,
                allowed_files=["harnesses/candidates/"],
                forbidden_files=["skills/", "src/agents/safety_gate/",
                                 "specs/harness/promotion_policy.md"],
                tests_to_run=["tests/unit/", "evals/"]),
            RepairAction(
                id="a2", action_type="add_test",
                target="tests/unit/test_regression_after_fix.py",
                reason="Add a regression test that locks the fixed behavior.",
                risk_level="low", requires_approval=False,
                allowed_files=["tests/"], forbidden_files=["skills/"],
                tests_to_run=["tests/unit/test_regression_after_fix.py"]),
        ],
        metadata={"unmet": list(analysis.unmet_criteria)},
    )


def _console_error_proposal(analysis) -> RepairProposal:
    pid = _proposal_id(MARKER_CONSOLE_ERROR)
    return RepairProposal(
        id=pid, failure_type="console_error", marker=MARKER_CONSOLE_ERROR,
        rationale="A console/fatal error remained after the change; propose a "
                  "candidate-side fix and a doc note (PROPOSAL ONLY).",
        actions=[
            RepairAction(
                id="a1", action_type="update_candidate",
                target="harnesses/candidates/<candidate-id>/",
                reason="Propose a fix so the post-patch console has no fatal error.",
                risk_level="medium", requires_approval=False,
                allowed_files=["harnesses/candidates/"],
                forbidden_files=["skills/", "src/agents/safety_gate/"],
                tests_to_run=["evals/"]),
            RepairAction(
                id="a2", action_type="update_docs",
                target="docs/repair_notes.md",
                reason="Record the console-error root cause and the proposed fix.",
                risk_level="low", requires_approval=False,
                allowed_files=["docs/"], forbidden_files=["skills/"],
                tests_to_run=[]),
        ],
        metadata={"unmet": list(analysis.unmet_criteria)},
    )


def _noop_proposal(analysis) -> RepairProposal:
    return RepairProposal(
        id=_proposal_id(""), failure_type=analysis.failure_type or "unknown", marker="",
        rationale="No known repair marker and no clear failure signal; propose no "
                  "change and ask a human to review (PROPOSAL ONLY).",
        actions=[RepairAction(
            id="a1", action_type="noop", target="docs/repair_notes.md",
            reason="No actionable repair; left for human review.",
            risk_level="low", requires_approval=False,
            allowed_files=["docs/"], forbidden_files=["skills/"], tests_to_run=[])],
        metadata={"unmet": list(analysis.unmet_criteria)},
    )


_BUILDERS = {
    MARKER_MISSING_ARTIFACT: _missing_artifact_proposal,
    MARKER_TEST_FAILED: _test_failed_proposal,
    MARKER_CONSOLE_ERROR: _console_error_proposal,
}


class FakeRepairPlanner:
    """Deterministic, offline repair planner. Never applies or executes anything."""

    planner_name = "fake_repair"

    def __init__(self, provider: FakeLLMProvider | None = None) -> None:
        self.provider = provider or FakeLLMProvider()
        if getattr(self.provider, "real_api_enabled", False):
            raise ValueError("FakeRepairPlanner refuses a provider with real_api_enabled=True")

    def _resolve_marker(self, analysis, marker: str) -> str:
        if marker in _KNOWN_MARKERS:
            return marker
        return _FAILURE_TYPE_MARKER.get(getattr(analysis, "failure_type", ""), "")

    def propose(self, analysis, marker: str = "") -> RepairProposal:
        resolved = self._resolve_marker(analysis, marker)

        # Exercise the offline fake provider (interface dependency); its response
        # is redacted before anything is kept, so nothing secret reaches a proposal.
        llm_request = LLMRequest(
            messages=[LLMMessage("user", f"repair failure_type={analysis.failure_type} "
                                         f"marker={resolved}")],
            metadata={"planner": "fake_repair"})
        _ = redact_text(self.provider.complete(llm_request).text)

        builder = _BUILDERS.get(resolved)
        proposal = builder(analysis) if builder else _noop_proposal(analysis)
        proposal.applied = False  # invariant: never applied here
        return proposal
