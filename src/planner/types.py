"""Planner types — pure dataclasses, no external dependencies, no secrets.

A plan is a *declarative* description of skill steps the harness could run. The
planner only produces these structures; it never executes them (see
`specs/planner/planner_contract.md`).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

RISK_LEVELS = ("low", "medium", "high")


@dataclass
class PlanStep:
    """A single, declarative step in a plan. Describes *what* to run, not how."""

    id: str
    skill: str
    inputs: dict = field(default_factory=dict)
    expected_outputs: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    risk_level: str = "low"  # one of RISK_LEVELS
    requires_approval: bool = False
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Plan:
    """An ordered set of declarative steps for a goal. Never auto-executed."""

    goal: str
    marker: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def skills(self) -> list[str]:
        return [s.skill for s in self.steps]

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "marker": self.marker,
            "steps": [s.to_dict() for s in self.steps],
            "metadata": dict(self.metadata),
        }


@dataclass
class PlanValidationResult:
    """Outcome of validating a plan. `valid` is True only when `errors` is empty."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors), "notes": list(self.notes)}


@dataclass
class PlannerRequest:
    """Input to a planner. Carries a goal and an optional explicit marker."""

    goal: str = ""
    marker: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class PlannerResponse:
    """Output of a planner: a plan plus *redacted* provider provenance."""

    plan: Plan
    provider: str = "fake"
    model: str = ""
    # The raw provider text, already redacted — safe to write to trace/report.
    raw_response_redacted: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "raw_response_redacted": self.raw_response_redacted,
            "notes": list(self.notes),
            "plan": self.plan.to_dict(),
        }
