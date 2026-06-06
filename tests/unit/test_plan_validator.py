import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.planner.plan_validator import validate_plan
from src.planner.types import Plan, PlanStep

# Built at runtime so no key-like literal lives in the test source.
SECRET = "sk-" + "a" * 40


def _step(id="s1", skill="inspect_project", risk="low", approval=False, deps=None, inputs=None):
    return PlanStep(id=id, skill=skill, risk_level=risk, requires_approval=approval,
                    depends_on=deps or [], inputs=inputs or {})


def test_valid_plan_pass():
    plan = Plan(goal="g", steps=[
        _step("a", "inspect_project"),
        _step("b", "patch_file_and_run_tests", risk="medium", deps=["a"]),
    ])
    res = validate_plan(plan)
    assert res.valid, res.errors


def test_duplicate_id_fail():
    plan = Plan(goal="g", steps=[_step("dup"), _step("dup", "patch_file_and_run_tests")])
    res = validate_plan(plan)
    assert not res.valid
    assert any("duplicate" in e for e in res.errors)


def test_missing_dependency_fail():
    plan = Plan(goal="g", steps=[_step("a", deps=["ghost"])])
    res = validate_plan(plan)
    assert not res.valid
    assert any("missing step" in e for e in res.errors)


def test_high_risk_without_approval_fail():
    plan = Plan(goal="g", steps=[_step("a", risk="high", approval=False)])
    res = validate_plan(plan)
    assert not res.valid
    assert any("requires_approval" in e for e in res.errors)


def test_high_risk_with_approval_pass():
    plan = Plan(goal="g", steps=[_step("a", risk="high", approval=True)])
    assert validate_plan(plan).valid


def test_illegal_risk_level_fail():
    plan = Plan(goal="g", steps=[_step("a", risk="extreme")])
    res = validate_plan(plan)
    assert not res.valid
    assert any("risk_level" in e for e in res.errors)


def test_direct_shell_skill_fail():
    for bad in ("raw_shell", "direct_command", "eval", "exec", "bash"):
        plan = Plan(goal="g", steps=[_step("a", skill=bad)])
        res = validate_plan(plan)
        assert not res.valid, bad
        assert any("forbidden direct-shell skill" in e for e in res.errors), bad


def test_forbidden_input_key_fail():
    plan = Plan(goal="g", steps=[_step("a", inputs={"shell": "rm -rf /"})])
    res = validate_plan(plan)
    assert not res.valid
    assert any("raw-command input key" in e for e in res.errors)


def test_secret_looking_input_fail():
    plan = Plan(goal="g", steps=[_step("a", inputs={"token": SECRET})])
    res = validate_plan(plan)
    assert not res.valid
    assert any("secret-looking" in e for e in res.errors)
    # the offending secret value is never echoed in the errors
    assert all(SECRET not in e for e in res.errors)


def test_empty_skill_fail():
    plan = Plan(goal="g", steps=[_step("a", skill="")])
    res = validate_plan(plan)
    assert not res.valid
    assert any("empty skill" in e for e in res.errors)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
