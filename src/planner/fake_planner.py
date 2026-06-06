"""FakePlanner — deterministic, offline planner backed only by FakeLLMProvider.

This planner turns a user goal / marker into a *declarative* `Plan`. It:

- uses ONLY the offline `FakeLLMProvider` (no network, no env reads, no real API);
- never executes a skill, shell command, or browser action — it only describes
  steps the harness *could* run later;
- redacts every provider response before it can be written to a trace/report.

Supported markers (also detected as substrings of the goal):
  - FAKE_PLAN_INSPECT_PROJECT     -> inspect-only plan
  - FAKE_PLAN_FULL_BROWSER_E2E    -> full real-browser e2e plan (pre/post patch)
  - FAKE_PLAN_PATCH_ONLY          -> patch + tests only
  - (no marker)                   -> a single, harmless noop plan
"""
from __future__ import annotations

from src.llm.fake_provider import FakeLLMProvider
from src.llm.redaction import redact_text
from src.llm.types import LLMMessage, LLMRequest
from src.planner.types import Plan, PlannerRequest, PlannerResponse, PlanStep

MARKER_INSPECT = "FAKE_PLAN_INSPECT_PROJECT"
MARKER_FULL_BROWSER = "FAKE_PLAN_FULL_BROWSER_E2E"
MARKER_PATCH_ONLY = "FAKE_PLAN_PATCH_ONLY"

_KNOWN_MARKERS = (MARKER_INSPECT, MARKER_FULL_BROWSER, MARKER_PATCH_ONLY)


def _resolve_marker(request: PlannerRequest) -> str:
    """Pick the marker from the explicit field, else detect it inside the goal."""
    if request.marker in _KNOWN_MARKERS:
        return request.marker
    goal = request.goal or ""
    for m in _KNOWN_MARKERS:
        if m in goal:
            return m
    return ""


def _inspect_plan(goal: str) -> Plan:
    return Plan(
        goal=goal,
        marker=MARKER_INSPECT,
        steps=[
            PlanStep(
                id="inspect",
                skill="inspect_project",
                inputs={"project_dir": "${project_dir}"},
                expected_outputs=["status", "project_type"],
                success_criteria=["project_inspected", "project_type_detected"],
                risk_level="low",
                requires_approval=False,
                depends_on=[],
            )
        ],
        metadata={"planner": "fake", "kind": "inspect"},
    )


def _patch_only_plan(goal: str) -> Plan:
    return Plan(
        goal=goal,
        marker=MARKER_PATCH_ONLY,
        steps=[
            PlanStep(
                id="inspect",
                skill="inspect_project",
                inputs={"project_dir": "${project_dir}"},
                expected_outputs=["status", "project_type"],
                success_criteria=["project_inspected"],
                risk_level="low",
                requires_approval=False,
                depends_on=[],
            ),
            PlanStep(
                id="patch",
                skill="patch_file_and_run_tests",
                inputs={"project_dir": "${project_dir}"},
                expected_outputs=["patch_applied", "tests_pass"],
                success_criteria=["source_file_patched", "tests_pass"],
                # Applies a source patch + runs tests in a sandbox: medium risk.
                risk_level="medium",
                requires_approval=False,
                depends_on=["inspect"],
            ),
        ],
        metadata={"planner": "fake", "kind": "patch_only"},
    )


def _full_browser_plan(goal: str) -> Plan:
    """Full real-browser e2e plan: server -> open/console (pre) -> patch ->
    RE-open/console (post). Mirrors evals/browser/full_browser_vite_login_bug_e2e.
    """
    return Plan(
        goal=goal,
        marker=MARKER_FULL_BROWSER,
        steps=[
            PlanStep(
                id="server",
                skill="start_local_server",
                inputs={"project_dir": "${project_dir}", "keep_alive": True},
                expected_outputs=["status", "server_url"],
                success_criteria=["server_started"],
                risk_level="medium",  # spawns a subprocess server
                requires_approval=False,
                depends_on=[],
            ),
            PlanStep(
                id="open_pre",
                skill="open_localhost_browser",
                inputs={"browser_mode": "playwright"},
                expected_outputs=["page_loaded", "browser_closed"],
                success_criteria=["real_browser_page_loaded"],
                risk_level="low",
                requires_approval=False,
                depends_on=["server"],
            ),
            PlanStep(
                id="console_pre",
                skill="read_browser_console",
                inputs={"browser_mode": "playwright"},
                expected_outputs=["console_counts"],
                success_criteria=["console_error_collected"],
                risk_level="low",
                requires_approval=False,
                depends_on=["open_pre"],
            ),
            PlanStep(
                id="patch",
                skill="patch_file_and_run_tests",
                inputs={"project_dir": "${project_dir}"},
                expected_outputs=["patch_applied", "tests_pass"],
                success_criteria=["patch_applied", "tests_pass"],
                risk_level="medium",
                requires_approval=False,
                depends_on=["console_pre"],
            ),
            PlanStep(
                id="open_post",
                skill="open_localhost_browser",
                inputs={"browser_mode": "playwright"},
                expected_outputs=["page_loaded", "browser_closed"],
                success_criteria=["real_browser_page_loaded"],
                risk_level="low",
                requires_approval=False,
                depends_on=["patch"],
            ),
            PlanStep(
                id="console_post",
                skill="read_browser_console",
                inputs={"browser_mode": "playwright"},
                expected_outputs=["console_counts"],
                success_criteria=["no_fatal_console_error_after_patch"],
                risk_level="low",
                requires_approval=False,
                depends_on=["open_post"],
            ),
        ],
        metadata={"planner": "fake", "kind": "full_browser_e2e"},
    )


def _noop_plan(goal: str) -> Plan:
    return Plan(
        goal=goal,
        marker="",
        steps=[
            PlanStep(
                id="noop",
                skill="noop",
                inputs={},
                expected_outputs=["decision"],
                success_criteria=["noop"],
                risk_level="low",
                requires_approval=False,
                depends_on=[],
            )
        ],
        metadata={"planner": "fake", "kind": "noop",
                  "reason": "no known marker; produced a harmless noop plan"},
    )


_BUILDERS = {
    MARKER_INSPECT: _inspect_plan,
    MARKER_FULL_BROWSER: _full_browser_plan,
    MARKER_PATCH_ONLY: _patch_only_plan,
}


class FakePlanner:
    """Deterministic planner. Uses FakeLLMProvider only; never executes a step."""

    planner_name = "fake"

    def __init__(self, provider: FakeLLMProvider | None = None) -> None:
        # Default to the offline fake provider. A non-fake provider is refused so
        # the planner can never reach a real API in this phase.
        self.provider = provider or FakeLLMProvider()
        if getattr(self.provider, "real_api_enabled", False):
            raise ValueError("FakePlanner refuses a provider with real_api_enabled=True")

    def plan(self, request: PlannerRequest) -> PlannerResponse:
        marker = _resolve_marker(request)

        # Exercise the (fake, offline) provider so the planner depends on the
        # provider interface — but the plan itself is built deterministically
        # from the marker. The provider response is redacted before it is kept,
        # so nothing secret-looking can ever reach a trace/report.
        llm_request = LLMRequest(
            messages=[LLMMessage("user", f"{request.goal}\nmarker={marker}")],
            metadata={"planner": "fake"},
        )
        llm_response = self.provider.complete(llm_request)
        raw_redacted = redact_text(llm_response.text)

        builder = _BUILDERS.get(marker)
        plan = builder(request.goal) if builder else _noop_plan(request.goal)

        notes = [] if marker else ["no known marker — produced a noop plan"]
        return PlannerResponse(
            plan=plan,
            provider=self.provider.provider_name,
            model=getattr(self.provider, "model", ""),
            raw_response_redacted=raw_redacted,
            notes=notes,
        )
