import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.planner.plan_renderer import render_json, render_markdown
from src.planner.plan_validator import validate_plan
from src.planner.types import Plan, PlanStep

SECRET = "sk-ant-" + "b" * 40


def _plan_with_secret():
    return Plan(goal=f"leak {SECRET} please", marker="", steps=[
        PlanStep(id="a", skill="inspect_project",
                 inputs={"note": f"key={SECRET}"}, success_criteria=["project_inspected"]),
        PlanStep(id="b", skill="patch_file_and_run_tests", risk_level="medium",
                 depends_on=["a"], success_criteria=["tests_pass"]),
    ])


def test_markdown_summary_redacted():
    plan = _plan_with_secret()
    md = render_markdown(plan, validate_plan(plan))
    assert SECRET not in md
    assert "***REDACTED***" in md
    # shows the structural fields
    assert "skill" in md and "depends_on" in md and "risk" in md
    assert "patch_file_and_run_tests" in md


def test_json_summary_redacted():
    plan = _plan_with_secret()
    js = render_json(plan, validate_plan(plan))
    assert SECRET not in js
    doc = json.loads(js)
    assert "plan" in doc and "validation" in doc
    assert doc["plan"]["steps"][0]["skill"] == "inspect_project"


def test_no_secret_output_clean_plan():
    plan = Plan(goal="clean", steps=[PlanStep(id="a", skill="inspect_project")])
    js = render_json(plan)
    md = render_markdown(plan)
    for blob in (js, md):
        assert SECRET not in blob


def test_markdown_notes_plan_only():
    plan = Plan(goal="g", steps=[PlanStep(id="a", skill="noop")])
    md = render_markdown(plan)
    assert "never executes" in md


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
