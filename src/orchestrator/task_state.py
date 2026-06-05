from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaskState:
    task_id: str
    user_goal: str
    status: str = "initialized"
    completed_steps: list[str] = field(default_factory=list)
    remaining_steps: list[str] = field(default_factory=list)
    shared_blackboard: dict = field(default_factory=dict)
