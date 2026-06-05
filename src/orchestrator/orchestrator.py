from __future__ import annotations

from pathlib import Path
from src.harness.trace_logger import TraceLogger
from src.orchestrator.task_state import TaskState


class Orchestrator:
    '''
    MVP rule-based orchestrator.

    Later versions can replace decision rules with:
    - ReCAP-style recursive planner
    - Skill graph compiler
    - Context router
    - LLM-based planner
    '''

    def __init__(self, task_id: str, user_goal: str):
        self.state = TaskState(task_id=task_id, user_goal=user_goal)
        self.logger = TraceLogger(task_id)

    def run_placeholder(self) -> Path:
        self.state.status = "completed"
        self.logger.event(
            actor={"agent_id": "orchestrator", "skill_id": None, "tool_name": None},
            input={"context_packet_ref": None, "user_visible_goal": self.state.user_goal, "tool_call": {"name": "placeholder", "args": {}}},
            output={"observation": "Placeholder orchestrator run completed.", "artifacts": [], "error": {"type": None, "message": None}},
            evaluation={"step_success": True, "verifier_result": "placeholder", "confidence": 1.0},
        )
        self.logger.write_score({
            "run_id": self.logger.run_id,
            "task_id": self.state.task_id,
            "task_success": True,
            "score": 1.0,
            "criteria_results": [],
            "forbidden_action_results": [],
            "metrics": {"total_steps": 1, "cli_command_count": 0, "browser_action_count": 0, "runtime_sec": 0, "token_cost": None, "safety_incidents": 0, "flaky": False},
            "failure": {"type": None, "root_cause": None, "recommended_fix": None},
        })
        self.logger.write_summary(f"# Run Summary\n\nTask `{self.state.task_id}` completed by placeholder orchestrator.\n")
        return self.logger.run_dir
