from src.harness.efficiency import (
    EfficiencyBudget,
    EfficiencyMetrics,
    budget_violations,
    cost_of_success,
    pareto_frontier,
    tool_efficiency,
)


def test_cost_of_success_none_on_failure():
    metrics = EfficiencyMetrics(total_steps=10)
    assert cost_of_success(False, metrics) is None


def test_budget_violations_detects_over_budget():
    metrics = EfficiencyMetrics(total_steps=31, cli_command_count=2)
    violations = budget_violations(metrics, EfficiencyBudget(max_steps=30))
    assert "max_steps" in violations


def test_tool_efficiency():
    metrics = EfficiencyMetrics(tool_call_count=4, useful_tool_call_count=3)
    assert tool_efficiency(metrics) == 0.75


def test_pareto_frontier_removes_dominated_candidate():
    candidates = [
        {"id": "a", "success_score": 1.0, "cost": 10.0},
        {"id": "b", "success_score": 1.0, "cost": 8.0},
        {"id": "c", "success_score": 0.8, "cost": 5.0},
    ]
    ids = {item["id"] for item in pareto_frontier(candidates)}
    assert "a" not in ids
    assert "b" in ids
    assert "c" in ids
