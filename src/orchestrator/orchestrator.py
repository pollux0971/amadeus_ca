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


# -- phase resolvers (support aliased pre/post-patch browser+console steps) --
def _pre_open(o):
    return o.get("open_pre") or o.get("open_localhost_browser") or {}


def _post_open(o):
    return o.get("open_post") or o.get("open_localhost_browser") or {}


def _pre_console(o):
    return o.get("console_pre") or o.get("read_browser_console") or {}


def _post_console(o):
    return o.get("console_post") or o.get("read_browser_console") or {}


def _console_error_collected(o):
    # Full e2e (aliased): the pre-patch console must have a real error / pageerror.
    if "console_pre" in o or "console_post" in o:
        c = _pre_console(o).get("console_counts", {})
        return c.get("error", 0) > 0 or c.get("fatal", 0) > 0
    # Legacy / vite: the console step produced a console_errors key.
    return "console_errors" in o.get("read_browser_console", {})


def _no_lingering(o):
    # Every browser/console step that ran must have closed its own resources.
    for out in o.values():
        if isinstance(out, dict) and "browser_closed" in out and out.get("browser_closed") is not True:
            return False
    return True


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
    "console_error_collected": _console_error_collected,
    "source_file_patched": lambda o: bool(
        o.get("patch_file_and_run_tests", {}).get("patch_applied")
    ),
    "patch_applied": lambda o: bool(o.get("patch_file_and_run_tests", {}).get("patch_applied"))
    and o.get("patch_file_and_run_tests", {}).get("status") not in ("failed", "not_implemented", None),
    "tests_pass": lambda o: bool(o.get("patch_file_and_run_tests", {}).get("test_passed")),
    "browser_has_no_fatal_console_error": lambda o: o.get("read_browser_console", {}).get(
        "fatal_error_count", 0
    )
    == 0,
    # open_localhost_browser keep-alive smoke
    "server_started": lambda o: o.get("start_local_server", {}).get("status") == "started"
    and bool(o.get("start_local_server", {}).get("server_url")),
    "browser_page_loaded": lambda o: o.get("open_localhost_browser", {}).get("status") == "loaded",
    "real_browser_page_loaded": lambda o: _pre_open(o).get("status") == "loaded"
    and _pre_open(o).get("is_real_browser") is True,
    # full real-browser e2e: post-patch re-verify + no fatal console error after patch
    "browser_reverify_passed": lambda o: _post_open(o).get("status") == "loaded"
    and _post_open(o).get("is_real_browser") is True,
    "no_fatal_console_error_after_patch": lambda o: _post_console(o).get("status") == "collected"
    and _post_console(o).get("console_counts", {}).get("fatal", 0) == 0,
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
    "no_lingering_server_process": _no_lingering,
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

        # Planner-category evals only *plan* — they never execute a skill, server,
        # browser, or patch. Route them to the isolated planner path.
        if (task or {}).get("category") == "planner":
            return self._run_planner_eval(task, run_dir, started)

        # planner_execution: build a fake plan, validate, bridge it to an
        # allowlisted skill sequence, and execute it under the Safety Gate. This
        # is NOT the plan-only `planner` category — it actually runs the skills.
        if (task or {}).get("category") == "planner_execution":
            return self._run_planner_execution_eval(task, run_dir, started, skills_dir)

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

    # ----------------------------------------------------------- planner eval

    def _run_planner_eval(self, task: dict, run_dir: Path, started: float) -> Path:
        """Run a planner-only eval: build + validate a plan, score its shape.

        No skill, server, browser, or patch is executed. Writes plan.json (the
        redacted plan), score.json, and summary.md.
        """
        import json as _json

        from src.planner.fake_planner import FakePlanner
        from src.planner.plan_renderer import render_json, render_markdown
        from src.planner.plan_validator import FORBIDDEN_SKILLS, validate_plan, _contains_secret
        from src.planner.types import PlannerRequest

        goal = task.get("goal") or task.get("user_goal") or ""
        marker = task.get("marker") or ""
        success_criteria = list(task.get("success_criteria") or [])

        planner = FakePlanner()  # offline fake provider; never executes a step
        response = planner.plan(PlannerRequest(goal=goal, marker=marker))
        plan = response.plan
        validation = validate_plan(plan)

        plan_json = render_json(plan, validation)
        (run_dir / "plan.json").write_text(plan_json, encoding="utf-8")

        skills = plan.skills
        order = list(skills)
        patch_idx = order.index("patch_file_and_run_tests") if "patch_file_and_run_tests" in order else -1
        post_patch_reverify = patch_idx >= 0 and "open_localhost_browser" in order[patch_idx + 1:]
        no_direct_shell = not any(str(s).strip().lower() in FORBIDDEN_SKILLS for s in skills)
        # The rendered plan is already redacted; if redaction would still change
        # it, a secret leaked — fail closed.
        no_secret_in_plan = not _contains_secret(plan_json)

        evidence = {
            "plan_created": bool(plan.steps),
            "plan_valid": validation.valid,
            "contains_start_local_server": "start_local_server" in skills,
            "contains_open_localhost_browser": "open_localhost_browser" in skills,
            "contains_read_browser_console": "read_browser_console" in skills,
            "contains_patch_file_and_run_tests": "patch_file_and_run_tests" in skills,
            "contains_post_patch_reverify": post_patch_reverify,
            "no_direct_shell_command": no_direct_shell,
            "no_secret_in_plan": no_secret_in_plan,
        }

        from src.llm.redaction import redact_text as _redact
        self.logger.event(
            actor={"type": "planner", "name": "fake"},
            input={"goal": _redact(goal), "marker": _redact(marker)},
            output={"plan_skills": skills, "valid": validation.valid,
                    "raw_response_redacted": response.raw_response_redacted},
            evaluation={"evidence": evidence},
        )

        criteria_results = evaluate_criteria(success_criteria, evidence)
        task_success = compute_task_success(criteria_results, [])
        passed = sum(1 for r in criteria_results if r["passed"])
        score_value = round(passed / len(criteria_results), 4) if criteria_results else (
            1.0 if task_success else 0.0)

        self.state.status = "completed" if task_success else "failed"
        unmet = [r["criterion"] for r in criteria_results if not r["passed"]]
        score = {
            "run_id": self.logger.run_id,
            "task_id": self.state.task_id,
            "task_success": task_success,
            "score": score_value,
            "criteria_results": criteria_results,
            "category": "planner",
            "executed": False,  # planner never executes a step
            "plan_skills": skills,
            "wall_time_ms": int((time.time() - started) * 1000),
            "failure": {} if task_success else {
                "root_cause": "planner plan did not satisfy: " + ", ".join(unmet),
                "category": "planner_plan_incomplete",
            },
        }
        self.logger.write_score(score)
        self.logger.write_summary(render_markdown(plan, validation))
        return run_dir

    # ------------------------------------------------- planner execution bridge

    def _run_planner_execution_eval(self, task: dict, run_dir: Path, started: float,
                                    skills_dir: str | Path) -> Path:
        """Build a fake plan, validate, bridge to an allowlisted sequence, run it.

        Fail-closed: an unvalidated plan, an un-allowlisted skill, or an
        unapproved high-risk step means NO execution. Writes plan.json,
        plan_execution_trace.jsonl, plan_execution_summary.md, score.json — all
        redacted, never any secret.
        """
        import json as _json

        from src.planner.fake_planner import FakePlanner
        from src.planner.plan_renderer import render_json
        from src.planner.plan_validator import validate_plan
        from src.planner.execution_bridge import (
            ALLOWLISTED_SKILLS, build_execution_sequence, execution_context_for,
        )
        from src.planner.types import PlannerRequest

        goal = task.get("goal") or task.get("user_goal") or ""
        marker = task.get("marker") or ""
        approve_high_risk = bool(task.get("approve_high_risk", False))
        success_criteria = list(task.get("success_criteria") or [])

        # 1) Build + validate the plan (fake, offline, deterministic).
        planner = FakePlanner()
        plan = planner.plan(PlannerRequest(goal=goal, marker=marker)).plan
        validation = validate_plan(plan)
        (run_dir / "plan.json").write_text(render_json(plan, validation), encoding="utf-8")

        # 2) Bridge: allowlist + approval. ok=False -> fail closed (no execution).
        bridge = build_execution_sequence(plan, validation, approve_high_risk=approve_high_risk)

        # 3) Merge the vetted, per-marker execution context (fixture/patch_plan/
        #    start_command). Explicit eval fields win; the planner never supplies
        #    a shell command — context is a fixed template keyed by the marker.
        ctx = execution_context_for(marker)
        merged = {**ctx, **task}
        self._eval_task = merged
        inner_criteria = list(merged.get("inner_success_criteria") or [])

        plan_skills = plan.skills
        allowed_skills_only = all(s in ALLOWLISTED_SKILLS for s in plan_skills) and bridge.ok
        # The bridge is a pure transform — building it executes nothing.
        execution_dry_run_safe = True

        outputs_by_skill: dict[str, dict] = {}
        executed_commands: list[str] = []
        metrics = EfficiencyMetrics()
        self.state.status = "running"
        self._server_sessions = []
        executed = False
        inner_score = 0.0

        # Trace the bridge decision before any execution.
        from src.llm.redaction import redact_text as _redact
        self.logger.event(
            actor={"type": "execution_bridge", "name": "plan_execution_bridge"},
            input={"goal": _redact(goal), "marker": _redact(marker),
                   "approve_high_risk": approve_high_risk},
            output=bridge.to_dict(),
            evaluation={"bridge_ok": bridge.ok},
            safety={"risk_level": "high" if any(s.risk_level == "high" for s in bridge.steps)
                    else "medium" if bridge.risk_notes else "low",
                    "blocked": not bridge.ok, "block_reason": None if bridge.ok else "bridge_fail_closed"},
        )

        if bridge.ok and validation.valid:
            fixture_path = (merged.get("fixture") or {}).get("path")
            project_dir = str((ROOT / fixture_path)) if fixture_path else None
            blackboard = {"project_dir": project_dir, "user_goal": self.state.user_goal}
            skills_path = skills_dir if Path(skills_dir).is_absolute() else ROOT / skills_dir
            candidates_path = None
            if self.candidates_dir:
                candidates_path = (self.candidates_dir if Path(self.candidates_dir).is_absolute()
                                   else ROOT / self.candidates_dir)
            executor = SkillExecutor(skills_path, candidates_dir=candidates_path)
            try:
                self._execute_sequence(bridge.required_skills, executor, blackboard,
                                       outputs_by_skill, executed_commands, metrics)
                executed = True
            finally:
                self._teardown_server_sessions()

            # Inner score from the real skill-evidence rules (same as a normal eval).
            inner_results = evaluate_criteria(
                inner_criteria, {c: self._evidence_for(c, outputs_by_skill) for c in inner_criteria})
            inner_passed = sum(1 for r in inner_results if r["passed"])
            inner_score = round(inner_passed / len(inner_results), 4) if inner_results else 0.0

        # 4) Bridge-level evidence (what the planner_execution eval scores).
        ran = set(outputs_by_skill.keys())
        order = [s.alias for s in bridge.steps]
        patch_idx = next((i for i, s in enumerate(bridge.steps)
                          if s.skill == "patch_file_and_run_tests"), -1)
        post_open_alias = next((s.alias for i, s in enumerate(bridge.steps)
                                if i > patch_idx and s.skill == "open_localhost_browser"), None)
        evidence = {
            "plan_created": bool(plan.steps),
            "plan_valid": validation.valid,
            "execution_dry_run_safe": execution_dry_run_safe,
            "allowed_skills_only": allowed_skills_only,
            "patch_skill_invoked": "patch_file_and_run_tests" in ran,
            "patch_file_and_run_tests_invoked": "patch_file_and_run_tests" in ran,
            "start_local_server_invoked": "start_local_server" in ran,
            "open_localhost_browser_invoked": any(
                s.skill == "open_localhost_browser" and s.alias in ran for s in bridge.steps),
            "read_browser_console_invoked": any(
                s.skill == "read_browser_console" and s.alias in ran for s in bridge.steps),
            "post_patch_reverify_invoked": bool(post_open_alias and post_open_alias in ran),
            "tests_pass": self._evidence_for("tests_pass", outputs_by_skill),
            "no_lingering_process": _no_lingering(outputs_by_skill),
            "score_1_0": executed and inner_score == 1.0,
            "no_secret_in_artifacts": self._artifacts_have_no_secret(run_dir),
        }

        criteria_results = evaluate_criteria(success_criteria, evidence)
        task_success = compute_task_success(criteria_results, [])
        passed = sum(1 for r in criteria_results if r["passed"])
        score_value = round(passed / len(criteria_results), 4) if criteria_results else (
            1.0 if task_success else 0.0)
        self.state.status = "completed" if task_success else "failed"

        unmet = [r["criterion"] for r in criteria_results if not r["passed"]]
        score = {
            "run_id": self.logger.run_id,
            "task_id": self.state.task_id,
            "task_success": task_success,
            "score": score_value,
            "criteria_results": criteria_results,
            "category": "planner_execution",
            "executed": executed,
            "bridge_ok": bridge.ok,
            "bridge_errors": list(bridge.errors),
            "risk_notes": list(bridge.risk_notes),
            "approved_high_risk": bridge.approved_high_risk,
            "inner_score": inner_score,
            "plan_skills": plan_skills,
            "executed_skills": sorted(ran),
            "wall_time_ms": int((time.time() - started) * 1000),
            "failure": {} if task_success else {
                "root_cause": "planner_execution did not satisfy: " + ", ".join(unmet),
                "category": "planner_execution_incomplete",
                "bridge_errors": list(bridge.errors),
            },
        }
        self.logger.write_score(score)

        # Dedicated, redacted plan-execution artifacts.
        from src.llm.redaction import redact_mapping
        events = []
        if self.logger.trace_path.exists():
            for line in self.logger.trace_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(redact_mapping(_json.loads(line)))
        (run_dir / "plan_execution_trace.jsonl").write_text(
            "\n".join(_json.dumps(e, ensure_ascii=False) for e in events) + ("\n" if events else ""),
            encoding="utf-8")
        self._write_plan_execution_summary(run_dir, task_success, score_value, marker,
                                           bridge, criteria_results, executed, inner_score)
        return run_dir

    @staticmethod
    def _artifacts_have_no_secret(run_dir: Path) -> bool:
        """Scan text artifacts in the run dir; True if none contains a secret."""
        from src.llm.redaction import redact_text
        for p in run_dir.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".zip"):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if redact_text(text) != text:
                return False
        return True

    def _write_plan_execution_summary(self, run_dir, task_success, score_value, marker,
                                      bridge, criteria_results, executed, inner_score) -> None:
        from src.llm.redaction import redact_text
        lines = ["# Plan Execution Summary", "",
                 f"- status: {'PASS' if task_success else 'FAIL'}",
                 f"- score: {score_value}",
                 f"- marker: {redact_text(marker) or '(none)'}",
                 f"- bridge_ok: {bridge.ok}",
                 f"- executed: {executed}",
                 f"- inner_score: {inner_score}",
                 f"- approved_high_risk: {bridge.approved_high_risk}", ""]
        if bridge.risk_notes:
            lines.append("## Risk notes")
            for n in bridge.risk_notes:
                lines.append(f"- {redact_text(n)}")
            lines.append("")
        if bridge.errors:
            lines.append("## Bridge errors (fail-closed)")
            for e in bridge.errors:
                lines.append(f"- {redact_text(e)}")
            lines.append("")
        lines.append("## Executable sequence (allowlisted)")
        lines.append("| plan_step | skill | alias | risk | approval |")
        lines.append("| --- | --- | --- | --- | --- |")
        for s in bridge.steps:
            lines.append(f"| {s.plan_step_id} | {s.skill} | {s.alias} | {s.risk_level} "
                         f"| {'yes' if s.requires_approval else 'no'} |")
        lines.append("")
        lines.append("## Criteria")
        for r in criteria_results:
            mark = "x" if r["passed"] else " "
            lines.append(f"- [{mark}] {r['criterion']}")
        lines.append("")
        lines.append("> Execution bridge — allowlisted skills only; no direct shell; "
                     "no autonomous replan.")
        text = "\n".join(lines) + "\n"
        (run_dir / "plan_execution_summary.md").write_text(text, encoding="utf-8")
        self.logger.write_summary(text)  # also the standard summary.md

    def _execute_sequence(self, required_skills, executor, blackboard,
                          outputs_by_skill, executed_commands, metrics) -> None:
        """Run an aliased skill sequence, logging a trace event per step.

        Shared by the normal eval path and the planner execution bridge so both
        execute skills identically (same Safety Gate check, same trace). The
        sequence is only ever a list the caller already validated/allowlisted.
        """
        for entry in required_skills:
            # A required-skills entry is a bare skill id, or {skill: <id>, as: <alias>}
            # so the same skill can run more than once (e.g. a pre-patch and a
            # post-patch browser/console step) and store its output under a label.
            if isinstance(entry, dict):
                skill_id = entry.get("skill") or entry.get("id")
                output_key = entry.get("as") or skill_id
            else:
                skill_id = entry
                output_key = entry

            inputs = self._build_inputs(skill_id, blackboard, outputs_by_skill)
            result = executor.run(skill_id, inputs)
            outputs_by_skill[output_key] = result.output
            blackboard.update(result.output)  # flat view for generic 1->N skills
            self.state.completed_steps.append(output_key)

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

    def _run_skills_and_score(self, required_skills, success_criteria, forbidden_actions,
                              scoring, executor, blackboard, outputs_by_skill,
                              executed_commands, metrics, run_dir, started, task) -> Path:
        self._execute_sequence(required_skills, executor, blackboard,
                               outputs_by_skill, executed_commands, metrics)

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
        browser_out = (outputs_by_skill.get("open_localhost_browser")
                       or outputs_by_skill.get("open_post")
                       or outputs_by_skill.get("open_pre") or {})
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

        from src.llm.redaction import redact_mapping

        # A task dict can carry a free-form goal/prompt; redact before it lands in
        # runs/ so no secret-looking value is ever persisted (no-secret-in-trace).
        (run_dir / "task.yaml").write_text(
            "# task spec snapshot (json-encoded, redacted)\n"
            + json.dumps(redact_mapping(task), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
