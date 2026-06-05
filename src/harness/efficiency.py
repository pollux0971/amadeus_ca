from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class EfficiencyBudget:
    max_steps: int = 30
    max_cli_commands: int = 10
    max_browser_actions: int = 20
    max_tool_calls: int = 30
    max_retries: int = 3
    max_replans: int = 5
    max_context_tokens: int = 12_000
    max_runtime_sec: float = 600.0


@dataclass
class EfficiencyMetrics:
    total_steps: int = 0
    cli_command_count: int = 0
    browser_action_count: int = 0
    tool_call_count: int = 0
    retry_count: int = 0
    replan_count: int = 0
    runtime_sec: float = 0.0
    context_tokens_estimated: int = 0
    useful_tool_call_count: int = 0
    redundant_tool_call_count: int = 0
    budget_violation_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def weighted_total_cost(metrics: EfficiencyMetrics, weights: dict[str, float] | None = None) -> float:
    """Compute a simple weighted cost for comparing harness candidates.

    This is intentionally transparent and tunable. It is not meant to be a universal metric.
    """
    w = {
        "total_steps": 1.0,
        "cli_command_count": 2.0,
        "browser_action_count": 2.0,
        "retry_count": 3.0,
        "context_tokens_estimated": 0.001,
        "runtime_sec": 0.1,
    }
    if weights:
        w.update(weights)
    return (
        w["total_steps"] * metrics.total_steps
        + w["cli_command_count"] * metrics.cli_command_count
        + w["browser_action_count"] * metrics.browser_action_count
        + w["retry_count"] * metrics.retry_count
        + w["context_tokens_estimated"] * metrics.context_tokens_estimated
        + w["runtime_sec"] * metrics.runtime_sec
    )


def cost_of_success(task_success: bool, metrics: EfficiencyMetrics, weights: dict[str, float] | None = None) -> float | None:
    if not task_success:
        return None
    return weighted_total_cost(metrics, weights)


def budget_violations(metrics: EfficiencyMetrics, budget: EfficiencyBudget) -> list[str]:
    checks = {
        "max_steps": metrics.total_steps <= budget.max_steps,
        "max_cli_commands": metrics.cli_command_count <= budget.max_cli_commands,
        "max_browser_actions": metrics.browser_action_count <= budget.max_browser_actions,
        "max_tool_calls": metrics.tool_call_count <= budget.max_tool_calls,
        "max_retries": metrics.retry_count <= budget.max_retries,
        "max_replans": metrics.replan_count <= budget.max_replans,
        "max_context_tokens": metrics.context_tokens_estimated <= budget.max_context_tokens,
        "max_runtime_sec": metrics.runtime_sec <= budget.max_runtime_sec,
    }
    return [name for name, ok in checks.items() if not ok]


def tool_efficiency(metrics: EfficiencyMetrics) -> float:
    if metrics.tool_call_count <= 0:
        return 1.0
    return metrics.useful_tool_call_count / max(metrics.tool_call_count, 1)


def pareto_frontier(candidates: Iterable[dict]) -> list[dict]:
    """Return non-dominated candidates.

    Candidate schema:
      {"id": str, "success_score": float, "cost": float}

    Higher success_score is better. Lower cost is better.
    """
    items = list(candidates)
    frontier: list[dict] = []
    for item in items:
        dominated = False
        for other in items:
            if other is item:
                continue
            if (
                other.get("success_score", 0) >= item.get("success_score", 0)
                and other.get("cost", float("inf")) <= item.get("cost", float("inf"))
                and (
                    other.get("success_score", 0) > item.get("success_score", 0)
                    or other.get("cost", float("inf")) < item.get("cost", float("inf"))
                )
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(item)
    return frontier
