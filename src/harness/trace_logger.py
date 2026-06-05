from __future__ import annotations

import json
import time
from pathlib import Path
from uuid import uuid4


class TraceLogger:
    def __init__(self, task_id: str, runs_dir: str | Path = "runs"):
        self.task_id = task_id
        self.run_id = f"{task_id}_{int(time.time())}_{uuid4().hex[:8]}"
        self.run_dir = Path(runs_dir) / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "artifacts").mkdir(exist_ok=True)
        (self.run_dir / "browser").mkdir(exist_ok=True)
        self.trace_path = self.run_dir / "trace.jsonl"

    def event(self, *, actor: dict, input: dict, output: dict, evaluation: dict | None = None, safety: dict | None = None, cost: dict | None = None) -> dict:
        step_id = f"step_{sum(1 for _ in self.trace_path.open('r', encoding='utf-8')) + 1:04d}" if self.trace_path.exists() else "step_0001"
        event = {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "step_id": step_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "actor": actor,
            "input": input,
            "output": output,
            "evaluation": evaluation or {},
            "safety": safety or {"risk_level": "low", "blocked": False, "block_reason": None},
            "cost": cost or {"tokens_in": None, "tokens_out": None, "wall_time_ms": 0},
        }
        with self.trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def write_summary(self, text: str) -> None:
        (self.run_dir / "summary.md").write_text(text, encoding="utf-8")

    def write_score(self, score: dict) -> None:
        (self.run_dir / "score.json").write_text(json.dumps(score, ensure_ascii=False, indent=2), encoding="utf-8")
