"""Planner package — turns a goal/marker into a *declarative*, validated plan.

Fake-only in this phase: the planner uses `FakeLLMProvider` (offline,
deterministic) and never executes a step. See `specs/planner/planner_contract.md`.
"""
from src.planner.types import (
    Plan,
    PlanStep,
    PlanValidationResult,
    PlannerRequest,
    PlannerResponse,
    RISK_LEVELS,
)
from src.planner.fake_planner import (
    FakePlanner,
    MARKER_INSPECT,
    MARKER_FULL_BROWSER,
    MARKER_PATCH_ONLY,
)
from src.planner.plan_validator import validate_plan, FORBIDDEN_SKILLS
from src.planner.plan_renderer import render_json, render_markdown

__all__ = [
    "Plan",
    "PlanStep",
    "PlanValidationResult",
    "PlannerRequest",
    "PlannerResponse",
    "RISK_LEVELS",
    "FakePlanner",
    "MARKER_INSPECT",
    "MARKER_FULL_BROWSER",
    "MARKER_PATCH_ONLY",
    "validate_plan",
    "FORBIDDEN_SKILLS",
    "render_json",
    "render_markdown",
]
