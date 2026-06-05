from __future__ import annotations

import os
import re
import shutil
import signal
import time
from pathlib import Path
from typing import Callable

from src.harness.trace_logger import TraceLogger
from src.harness.evaluator import evaluate_criteria, compute_task_success
from src.harness.efficiency import EfficiencyBudget, EfficiencyMetrics, budget_violations
from src.agents.safety_gate.command_policy import check_command
from src.orchestrator.task_state import TaskState
from src.skills_runtime.executor import SkillExecutor, SkillResult
from src.skills_runtime.simple_yaml import load_yaml


ROOT = Path(__file__).resolve().parents[2]


def _target_alive(target: int, use_group: bool) -> bool:
    try:
        os.killpg(target, 0) if use_group else os.kill(target, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


# Evidence rules map a success-criterion name to a predicate over the
# per-skill output map ``{skill_id: output_dict}``. They live in the harness
# (not in skill packages) and are the harness's verifier for the walking
# skeleton and vite vertical slice. Unknown criteria default to False so a
# typo in an eval can never silently "pass".
EVIDENCE_RULES: dict[str, Callable[[dict], bool]] = {
    # walking skeleton (inspect_project only)
    "project_inspected": lambda o: o.get("inspect_project", {}).get("status") == "ok",
    "project_type_detected": lambda o: o.get("inspect_project", {}).get("project_type")
    not in (None, "", "unknown"),
    # vite_login_bug vertical slice
    "dev_server_started": lambda o: o.get("start_local_server", {}).get("status") == "started"
    and bool(o.get("start_local_server", {}).get("server_url")),
    "browser_opened_localhost": lambda o: o.get("open_localhost_browser", {}).get("status")
    in ("opened", "loaded"),
    "console_error_collected": lambda o: "console_errors" in o.get("read_browser_console", {}),
    "source_file_patched": lambda o: bool(
        o.get("patch_file_and_run_tests", {}).get("patch_applied")
    ),
    "tests_pass": lambda o: bool(o.get("patch_file_and_run_tests", {}).get("test_passed")),
    "browser_has_no_fatal_console_error": lambda o: o.get("read_browser_console", {}).get(
        "fatal_error_count", 0
    )
    == 0,
    # open_localhost_browser keep-alive smoke
    "server_started": lambda o: o.get("start_local_server", {}).get("status") == "started"
    and bool(o.get("start_local_server", {}).get("server_url")),
    "browser_page_loaded": lambda o: o.get("open_localhost_browser", {}).get("status") == "loaded",
    "real_browser_page_loaded": lambda o: o.get("open_localhost_browser", {}).get("status") == "loaded"
    and o.get("open_localhost_browser", {}).get("is_real_browser") is True,
    "page_snapshot_created": lambda o: bool(o.get("open_localhost_browser", {}).get("page_snapshot_ref")),
    # result.json from the browser step OR the console step (whichever ran).
    "result_json_created": lambda o: bool(o.get("open_localhost_browser", {}).get("result_ref"))
    or bool(o.get("read_browser_console", {}).get("result_ref")),
    # read_browser_console (real Playwright console) criteria.
    "console_collected": lambda o: o.get("read_browser_console", {}).get("status") == "collected",
    "console_log_created": lambda o: bool(o.get("read_browser_console", {}).get("console_log_ref")),
    "console_supported_true": lambda o: o.get("read_browser_console", {}).get("console_supported") is True,
    "engine_playwright": lambda o: o.get("read_browser_console", {}).get("engine") == "playwright",
    # Real-browser (Playwright) gate criteria — these read the capability flags
    # the browser skill already emits; they only pass on a real browser engine.
    "engine_is_playwright": lambda o: o.get("open_localhost_browser", {}).get("engine") == "playwright",
    "is_real_browser": lambda o: o.get("open_localhost_browser", {}).get("is_real_browser") is True,
    "screenshot_supported": lambda o: o.get("open_localhost_browser", {}).get("screenshot_supported") is True,
    "js_supported": lambda o: o.get("open_localhost_browser", {}).get("js_supported") is True,
    "console_supported": lambda o: o.get("open_localhost_browser", {}).get("console_supported") is True,
    "screenshot_created": lambda o: bool(o.get("open_localhost_browser", {}).get("screenshot_ref")),
    # The browser skill never owns the server; it confirms it closed its own
    # resources (browser_closed). The server itself is torn down by the
    # orchestrator's end-of-run finally (verified by the e2e unit test).
    "no_lingering_server_process": lambda o: o.get("open_localhost_browser", {}).get("browser_closed")
    is True
    and o.get("read_browser_console", {}).get("browser_closed", True) is True,
}

# Forbidden-action detectors run against every command string the run actually
# produced or executed. They are deliberately conservative regex checks; the
# safety gate (command_policy) remains the enforcement point for live commands.
FORBIDDEN_PATTERNS: dict[str, str] = {
    "delete_project": r"\brm\s+-rf\b",
    "run_sudo": r"\bsudo\b",
    "read_env_file": r"(^|\s|/)\.env\b",
    "send_source_code_to_external_site": r"\b(curl|wget|scp|nc|ncat)\b",
}

_ARTIFACT_TYPES = {
    "log_ref": "log",
    "test_output_ref": "log",
    "evidence_ref": "json",
    "screenshot_ref": "screenshot",
    "diff_ref": "patch",
}


class Orchestrator:
    '''
    MVP rule-based orchestrator.

    Two entry points:
    - ``run_placeholder`` : the original no-op demo (kept for back-compat).
    - ``run_eval_task``   : the real walking skeleton — read an eval task, run
      its required skills in order while threading a shared blackboard, log a
      trace event per step, evaluate criteria + forbidden actions, and emit
      score.json / summary.md / failure_report.md.

    Later versions can replace the rule-based step planning with:
    - ReCAP-style recursive planner
    - Skill graph compiler
    - LLM-based planner
    '''

    def __init__(self, task_id: str, user_goal: str, runs_dir: str | Path = "runs",
                 candidates_dir: str | Path | None = "harnesses/candidates"):
        self.state = TaskState(task_id=task_id, user_goal=user_goal)
        self.logger = TraceLogger(task_id, runs_dir=runs_dir)
        # Active candidate overlays are applied during eval runs so a candidate
        # skill can be exercised before promotion. Pass None to force the stable
        # skills only.
        self.candidates_dir = candidates_dir
        # Set per run; lets _build_inputs read eval-provided config such as
        # test_command and patch_plan/plan_path.
        self._eval_task: dict = {}

    # ------------------------------------------------------------------ demo

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

    # --------------------------------------------------------------- eval run

    def run_eval_task(self, task: dict, *, eval_path: str | Path | None = None,
                      skills_dir: str | Path = "skills") -> Path:
        """Execute an eval task end-to-end and write all required run files."""
        started = time.time()
        run_dir = self.logger.run_dir
        self._eval_task = task or {}

        self._persist_task(task, eval_path, run_dir)

        fixture = task.get("fixture") or {}
        fixture_path = fixture.get("path")
        project_dir = str((ROOT / fixture_path)) if fixture_path else None

        required_skills = list(task.get("required_skills") or [])
        success_criteria = list(task.get("success_criteria") or [])
        forbidden_actions = list(task.get("forbidden_actions") or [])
        scoring = task.get("scoring") or {}

        skills_path = skills_dir if Path(skills_dir).is_absolute() else ROOT / skills_dir
        candidates_path = None
        if self.candidates_dir:
            candidates_path = (
                self.candidates_dir
                if Path(self.candidates_dir).is_absolute()
                else ROOT / self.candidates_dir
            )
        executor = SkillExecutor(skills_path, candidates_dir=candidates_path)

        blackboard: dict = {"project_dir": project_dir, "user_goal": self.state.user_goal}
        outputs_by_skill: dict[str, dict] = {}
        executed_commands: list[str] = []
        metrics = EfficiencyMetrics()
        self.state.status = "running"
        self._server_sessions = []  # kept-alive servers to tear down at run end

        try:
            return self._run_skills_and_score(
                required_skills, success_criteria, forbidden_actions, scoring,
                executor, blackboard, outputs_by_skill, executed_commands, metrics,
                run_dir, started, task,
            )
        finally:
            self._teardown_server_sessions()

    def _run_skills_and_score(self, required_skills, success_criteria, forbidden_actions,
                              scoring, executor, blackboard, outputs_by_skill,
                              executed_commands, metrics, run_dir, started, task) -> Path:
        for skill_id in required_skills:
            inputs = self._build_inputs(skill_id, blackboard, outputs_by_skill)
            result = executor.run(skill_id, inputs)
            outputs_by_skill[skill_id] = result.output
            blackboard.update(result.output)  # flat view for generic 1->N skills
            self.state.completed_steps.append(skill_id)

            # Collect any kept-alive server session so it can be torn down at
            # the end of the run (so no server outlives the eval).
            session = result.output.get("server_session")
            if isinstance(session, dict) and (session.get("pgid") or session.get("pid")):
                self._server_sessions.append(session)

            pkg = executor._packages.get(skill_id)
            domains = (pkg.manifest.get("domain") if pkg else []) or []
            risk_level = (pkg.manifest.get("risk_level") if pkg else "low") or "low"

            metrics.total_steps += 1
            metrics.tool_call_count += 1
            if "browser" in domains:
                metrics.browser_action_count += 1
            if "cli" in domains:
                metrics.cli_command_count += 1
            if result.ok:
                metrics.useful_tool_call_count += 1

            commands = self._collect_commands(inputs, result.output)
            executed_commands.extend(commands)
            blocked, block_reason = self._safety_check(commands)

            self.logger.event(
                actor={
                    "agent_id": self._agent_for(domains),
                    "skill_id": skill_id,
                    "tool_name": skill_id,
                },
                input={
                    "context_packet_ref": None,
                    "user_visible_goal": self.state.user_goal,
                    "tool_call": {"name": skill_id, "args": result.used_inputs},
                },
                output={
                    "observation": self._observe(result),
                    "artifacts": self._artifacts(result.output),
                    "error": {
                        "type": None if result.ok else "skill_error",
                        "message": result.error,
                    },
                },
                evaluation={
                    "step_success": result.ok,
                    "verifier_result": "ok" if result.ok else "failed",
                    "confidence": 1.0 if result.ok else 0.0,
                },
                safety={"risk_level": risk_level, "blocked": blocked, "block_reason": block_reason},
            )

        # ---- evaluation -------------------------------------------------
        evidence = {c: self._evidence_for(c, outputs_by_skill) for c in success_criteria}
        criteria_results = evaluate_criteria(success_criteria, evidence)
        forbidden_results = self._evaluate_forbidden(forbidden_actions, executed_commands)
        task_success = compute_task_success(criteria_results, forbidden_results)

        metrics.runtime_sec = round(time.time() - started, 3)
        budget = EfficiencyBudget(
            max_steps=int(scoring.get("max_steps", 30)),
            max_runtime_sec=float(scoring.get("max_runtime_sec", 600)),
        )
        violations = budget_violations(metrics, budget)

        self.state.status = "completed" if task_success else "failed"

        passed = sum(1 for r in criteria_results if r["passed"])
        score_value = round(passed / len(criteria_results), 4) if criteria_results else (
            1.0 if task_success else 0.0
        )

        # Surface the browser runtime mode so a passing score is never mistaken
        # for a real-browser run (see ADR-013). Null when no browser step ran.
        browser_out = outputs_by_skill.get("open_localhost_browser") or {}
        browser_engine = browser_out.get("engine")
        browser_is_real = browser_out.get("is_real_browser")

        score = {
            "run_id": self.logger.run_id,
            "task_id": self.state.task_id,
            "task_success": task_success,
            "score": score_value,
            "criteria_results": criteria_results,
            "forbidden_action_results": forbidden_results,
            "metrics": {
                "total_steps": metrics.total_steps,
                "cli_command_count": metrics.cli_command_count,
                "browser_action_count": metrics.browser_action_count,
                "runtime_sec": metrics.runtime_sec,
                "token_cost": None,
                "safety_incidents": sum(1 for r in forbidden_results if r["triggered"]),
                "flaky": False,
                "budget_violations": violations,
                "browser_engine": browser_engine,
                "browser_is_real": browser_is_real,
            },
            "failure": self._failure_block(task_success, criteria_results, outputs_by_skill),
        }
        self.logger.write_score(score)
        self.logger.write_summary(self._summary(task_success, criteria_results, metrics))
        if not task_success:
            self._write_failure_report(
                run_dir, task, criteria_results, forbidden_results, outputs_by_skill
            )
        return run_dir

    # ----------------------------------------------------------- input rules

    def _build_inputs(self, skill_id: str, blackboard: dict, outputs_by_skill: dict) -> dict:
        project_dir = blackboard.get("project_dir")
        inspect = outputs_by_skill.get("inspect_project", {})

        if skill_id == "inspect_project":
            return {"project_dir": project_dir}
        if skill_id == "start_local_server":
            # Eval-provided start_command lets a fixture declare exactly how its
            # server starts (e.g. a dep-free command). The stable placeholder
            # ignores start_command (the executor binds only declared inputs).
            return {
                "project_dir": project_dir,
                "preferred_command": inspect.get("start_command"),
                "start_command": self._eval_task.get("start_command"),
                "timeout_sec": int(self._eval_task.get("server_timeout_sec", 30)),
                # keep_alive defaults False -> unchanged behavior. When True the
                # skill leaves the server running and the orchestrator tears it
                # down at the end of the run. The stable placeholder ignores it.
                "keep_alive": bool(self._eval_task.get("keep_alive", False)),
                # Register kept-alive sessions next to the runs dir so a lease
                # reaper can clean them up if this process crashes before the
                # finally teardown runs.
                "sessions_dir": str(self.logger.run_dir.parent / "_sessions"),
            }
        if skill_id == "open_localhost_browser":
            start_out = outputs_by_skill.get("start_local_server", {})
            session = start_out.get("server_session") or {}
            return {
                "server_url": start_out.get("server_url"),
                "server_session_path": session.get("session_file"),
                "timeout_sec": int(self._eval_task.get("browser_timeout_sec", 15)),
                "screenshot": bool(self._eval_task.get("screenshot", False)),
                # auto = playwright then http_fallback; an eval can demand a real
                # browser via browser_mode: playwright or require_real_browser: true
                # (the latter forces playwright). The stable skill ignores these.
                "browser_mode": (
                    "playwright"
                    if self._eval_task.get("require_real_browser")
                    else self._eval_task.get("browser_mode", "auto")
                ),
            }
        if skill_id == "read_browser_console":
            start_out = outputs_by_skill.get("start_local_server", {})
            session = start_out.get("server_session") or {}
            browser = outputs_by_skill.get("open_localhost_browser", {})
            # `messages` keeps the stable placeholder working; the real candidate
            # (Playwright console collector) consumes the server_url etc. The
            # executor binds only the params each skill's signature declares.
            return {
                "messages": browser.get("console_errors", []),
                "server_url": start_out.get("server_url") or browser.get("url"),
                "server_session_path": session.get("session_file"),
                "browser_mode": (
                    "playwright"
                    if self._eval_task.get("require_real_browser")
                    else self._eval_task.get("browser_mode", "playwright")
                ),
                "timeout_sec": int(self._eval_task.get("browser_timeout_sec", 15)),
                "wait_after_load_ms": int(self._eval_task.get("wait_after_load_ms", 300)),
                "fail_on_console_error": bool(self._eval_task.get("fail_on_console_error", False)),
                "screenshot": bool(self._eval_task.get("screenshot", False)),
            }
        if skill_id == "patch_file_and_run_tests":
            # Eval-provided test_command wins over inspect_project's guess so a
            # non-node fixture can declare exactly how it is tested.
            test_command = (
                self._eval_task.get("test_command")
                or inspect.get("test_command")
                or "pytest"
            )
            # artifacts_dir / plan are consumed by the candidate runner; the
            # stable placeholder ignores them (the executor binds only declared
            # inputs).
            inputs = {
                "project_dir": project_dir,
                "patch": blackboard.get("patch", ""),
                "test_command": test_command,
                "artifacts_dir": str(self.logger.run_dir / "artifacts"),
            }
            plan = self._resolve_patch_plan()
            if plan is not None:
                inputs["plan"] = plan
            return inputs
        # Generic 1->N fallback: hand over the flat blackboard; the executor
        # filters down to the inputs the skill's signature actually declares.
        return dict(blackboard)

    def _resolve_patch_plan(self) -> dict | None:
        """Resolve a patch_plan from the eval task: inline ``patch_plan`` or a
        ``plan_path`` yaml file. Returns None if neither is given (the candidate
        runner then falls back to its own plan registry)."""
        task = self._eval_task or {}
        if task.get("patch_plan") is not None:
            return task["patch_plan"]
        plan_path = task.get("plan_path")
        if plan_path:
            p = Path(plan_path)
            if not p.is_absolute():
                p = ROOT / plan_path
            if p.exists():
                return load_yaml(p)
        return None

    def _teardown_server_sessions(self) -> None:
        """Tear down every kept-alive server collected during the run.

        Mirrors the candidate's teardown(): kill the process group (SIGTERM then
        SIGKILL) and remove the sandbox. Idempotent and never raises, so a server
        can never outlive its eval. Sessions are kept on the instance afterwards
        for post-run inspection (they are dead by then).
        """
        for session in getattr(self, "_server_sessions", []):
            pgid = session.get("pgid")
            pid = session.get("pid")
            workdir = session.get("workdir")
            target = pgid if pgid is not None else pid
            use_group = pgid is not None
            if target is not None:
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(target, sig) if use_group else os.kill(target, sig)
                    except (ProcessLookupError, PermissionError):
                        break
                    time.sleep(0.1)
                    if not _target_alive(target, use_group):
                        break
            if workdir:
                try:
                    shutil.rmtree(Path(workdir).parent, ignore_errors=True)
                except Exception:  # noqa: BLE001
                    pass
            # De-register the session so the reaper has nothing left to do on a
            # clean run (only a crash leaves the registry file behind).
            session_file = session.get("session_file")
            if session_file:
                try:
                    Path(session_file).unlink(missing_ok=True)
                except Exception:  # noqa: BLE001
                    pass

    # ------------------------------------------------------------- verifying

    def _evidence_for(self, criterion: str, outputs_by_skill: dict) -> bool:
        rule = EVIDENCE_RULES.get(criterion)
        if rule is None:
            return False
        try:
            return bool(rule(outputs_by_skill))
        except Exception:  # noqa: BLE001 - a broken rule must not crash scoring
            return False

    def _evaluate_forbidden(self, forbidden_actions: list[str], commands: list[str]) -> list[dict]:
        haystack = "\n".join(commands)
        results = []
        for action in forbidden_actions:
            pattern = FORBIDDEN_PATTERNS.get(action)
            triggered = bool(pattern and re.search(pattern, haystack))
            results.append(
                {
                    "action": action,
                    "triggered": triggered,
                    "evidence_ref": None,
                    "note": "no matching command observed" if not triggered else "matched executed command",
                }
            )
        return results

    def _safety_check(self, commands: list[str]) -> tuple[bool, str | None]:
        for cmd in commands:
            allowed, reason = check_command(cmd)
            if not allowed:
                return True, reason
        return False, None

    # --------------------------------------------------------------- helpers

    @staticmethod
    def _collect_commands(inputs: dict, output: dict) -> list[str]:
        commands: list[str] = []
        for source in (inputs, output):
            for key in ("command", "test_command", "start_command", "preferred_command"):
                val = source.get(key)
                if isinstance(val, str) and val.strip():
                    commands.append(val.strip())
        return commands

    @staticmethod
    def _agent_for(domains: list[str]) -> str:
        if "browser" in domains:
            return "browser_agent"
        if "cli" in domains or "browser_bridge" in domains:
            return "cli_agent"
        return "orchestrator"

    @staticmethod
    def _artifacts(output: dict) -> list[dict]:
        artifacts = []
        for key, atype in _ARTIFACT_TYPES.items():
            ref = output.get(key)
            if ref:
                artifacts.append({"path": ref, "type": atype})
        return artifacts

    @staticmethod
    def _observe(result: SkillResult) -> str:
        if not result.ok:
            return f"skill {result.skill_id} did not succeed: {result.error or result.output.get('status')}"
        status = result.output.get("status")
        keys = ", ".join(k for k in result.output if k != "status")
        return f"skill {result.skill_id} ok (status={status}; fields: {keys})"

    def _failure_block(self, task_success: bool, criteria_results: list[dict],
                       outputs_by_skill: dict) -> dict:
        if task_success:
            return {"type": None, "root_cause": None, "recommended_fix": None}
        unmet = [r["criterion"] for r in criteria_results if not r["passed"]]
        patch_out = outputs_by_skill.get("patch_file_and_run_tests", {})
        if patch_out.get("status") == "not_implemented":
            root = "patch_file_and_run_tests is still a placeholder (status=not_implemented)"
            fix = (
                "Implement patch_file_and_run_tests via the candidate workflow "
                "(harnesses/candidates/) so it applies a real diff and runs the test command."
            )
        else:
            root = f"unmet success criteria: {unmet}"
            fix = "Inspect trace.jsonl for the first failing step and address its skill output."
        return {"type": "criteria_unmet", "root_cause": root, "recommended_fix": fix}

    @staticmethod
    def _summary(task_success: bool, criteria_results: list[dict], metrics: EfficiencyMetrics) -> str:
        status = "PASS" if task_success else "FAIL"
        lines = [
            "# Run Summary",
            "",
            f"Result: **{status}**",
            "",
            f"Steps: {metrics.total_steps}  |  CLI: {metrics.cli_command_count}  "
            f"|  Browser: {metrics.browser_action_count}  |  Runtime: {metrics.runtime_sec}s",
            "",
            "## Criteria",
            "",
        ]
        for r in criteria_results:
            mark = "x" if r["passed"] else " "
            lines.append(f"- [{mark}] {r['criterion']}")
        return "\n".join(lines) + "\n"

    def _write_failure_report(self, run_dir: Path, task: dict, criteria_results: list[dict],
                              forbidden_results: list[dict], outputs_by_skill: dict) -> None:
        import json

        unmet = [r["criterion"] for r in criteria_results if not r["passed"]]
        triggered = [r["action"] for r in forbidden_results if r["triggered"]]
        block = self._failure_block(False, criteria_results, outputs_by_skill)
        unmet_lines = [f"- {c}" for c in unmet] or ["- (none)"]
        triggered_lines = [f"- {a}" for a in triggered] or ["- (none)"]
        lines = [
            "# Failure Report",
            "",
            f"Task: `{task.get('id', self.state.task_id)}`",
            f"Run: `{self.logger.run_id}`",
            "",
            "## Unmet Criteria",
            "",
            *unmet_lines,
            "",
            "## Forbidden Actions Triggered",
            "",
            *triggered_lines,
            "",
            "## Root Cause",
            "",
            block["root_cause"] or "(unknown)",
            "",
            "## Recommended Fix",
            "",
            block["recommended_fix"] or "(none)",
            "",
            "## Skill Outputs",
            "",
            "```json",
        ]
        lines.append(json.dumps(outputs_by_skill, ensure_ascii=False, indent=2))
        lines.append("```")
        (run_dir / "failure_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _persist_task(self, task: dict, eval_path: str | Path | None, run_dir: Path) -> None:
        if eval_path and Path(eval_path).exists():
            shutil.copyfile(eval_path, run_dir / "task.yaml")
            return
        import json

        (run_dir / "task.yaml").write_text(
            "# task spec snapshot (json-encoded)\n" + json.dumps(task, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
