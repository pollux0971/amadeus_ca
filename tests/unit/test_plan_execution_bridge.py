import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.planner.execution_bridge import (
    ALLOWLISTED_SKILLS,
    build_execution_sequence,
    execution_context_for,
)
from src.planner.fake_planner import FakePlanner, MARKER_FULL_BROWSER, MARKER_PATCH_ONLY
from src.planner.plan_validator import validate_plan
from src.planner.types import Plan, PlannerRequest, PlanStep

SECRET = "sk-" + "e" * 40


def _fake_plan(marker):
    return FakePlanner().plan(PlannerRequest(marker=marker)).plan


def test_valid_plan_converts_to_executable_sequence():
    plan = _fake_plan(MARKER_FULL_BROWSER)
    res = build_execution_sequence(plan, validate_plan(plan))
    assert res.ok, res.errors
    skills = [s["skill"] for s in res.required_skills]
    assert skills == ["start_local_server", "open_localhost_browser",
                      "read_browser_console", "patch_file_and_run_tests",
                      "open_localhost_browser", "read_browser_console"]
    # repeated skills keep their step id as alias (pre/post); unique keep name
    aliases = [s["as"] for s in res.required_skills]
    assert aliases == ["start_local_server", "open_pre", "console_pre",
                       "patch_file_and_run_tests", "open_post", "console_post"]


def test_invalid_plan_rejected():
    plan = Plan(goal="g", steps=[PlanStep(id="dup", skill="inspect_project"),
                                 PlanStep(id="dup", skill="inspect_project")])
    res = build_execution_sequence(plan)  # validates internally
    assert not res.ok
    assert any("plan_not_validated" in e for e in res.errors)


def test_unknown_skill_rejected():
    plan = Plan(goal="g", steps=[PlanStep(id="a", skill="some_unknown_tool")])
    res = build_execution_sequence(plan, validate_plan(plan))
    assert not res.ok
    assert any("skill_not_allowlisted" in e for e in res.errors)


def test_direct_shell_rejected():
    for bad in ("raw_shell", "direct_command", "eval", "exec", "bash"):
        plan = Plan(goal="g", steps=[PlanStep(id="a", skill=bad)])
        res = build_execution_sequence(plan, validate_plan(plan))
        assert not res.ok, bad
        # rejected either as forbidden or as not-allowlisted (both fail closed)
        assert any(("forbidden_skill" in e or "skill_not_allowlisted" in e or "validation" in e)
                   for e in res.errors), bad


def test_high_risk_without_approval_rejected():
    plan = Plan(goal="g", steps=[PlanStep(id="a", skill="inspect_project",
                                          risk_level="high", requires_approval=True)])
    res = build_execution_sequence(plan, validate_plan(plan), approve_high_risk=False)
    assert not res.ok
    assert any("high_risk_without_approval" in e for e in res.errors)


def test_high_risk_with_approval_allowed():
    plan = Plan(goal="g", steps=[PlanStep(id="a", skill="inspect_project",
                                          risk_level="high", requires_approval=True)])
    res = build_execution_sequence(plan, validate_plan(plan), approve_high_risk=True)
    assert res.ok, res.errors
    assert res.approved_high_risk is True


def test_allowlisted_skills_pass():
    steps = [PlanStep(id=s, skill=s) for s in ALLOWLISTED_SKILLS]
    plan = Plan(goal="g", steps=steps)
    res = build_execution_sequence(plan, validate_plan(plan))
    assert res.ok, res.errors
    assert len(res.required_skills) == len(ALLOWLISTED_SKILLS)


def test_original_plan_not_mutated():
    plan = _fake_plan(MARKER_FULL_BROWSER)
    before = copy.deepcopy(plan.to_dict())
    build_execution_sequence(plan, validate_plan(plan))
    assert plan.to_dict() == before


def test_redaction_applied_to_bridge_dict():
    # a (hypothetical) secret in a plan input is redacted in the bridge's dict
    plan = Plan(goal=f"leak {SECRET}", steps=[
        PlanStep(id="a", skill="inspect_project", inputs={"note": SECRET})])
    res = build_execution_sequence(plan, validate_plan(plan))
    # validation fails on the secret input, so it never executes; the bridge dict
    # is still redaction-safe
    import json
    blob = json.dumps(res.to_dict())
    assert SECRET not in blob


def test_execution_context_only_for_known_markers():
    assert execution_context_for(MARKER_FULL_BROWSER)  # non-empty
    assert execution_context_for(MARKER_PATCH_ONLY)
    assert execution_context_for("FAKE_PLAN_INSPECT_PROJECT") == {}
    assert execution_context_for("") == {}
    # returns a copy — mutating it does not affect the registry
    ctx = execution_context_for(MARKER_FULL_BROWSER)
    ctx["fixture"] = {"path": "tampered"}
    assert execution_context_for(MARKER_FULL_BROWSER)["fixture"]["path"] != "tampered"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
