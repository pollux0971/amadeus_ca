"""ProviderBackedPlanner — a provider-aware planner (fake default, real opt-in only).

This wraps ANY `LLMProvider` (fake or real) behind the existing planner interface.
It is still **plan-only** — it never executes a step — and it never makes a real API
call unless explicitly opted in (`allow_real_call=True`, NOT this phase):

  - A fake provider (real_api_enabled=False) is exercised offline (safe), exactly
    like `FakePlanner`.
  - A real provider (real_api_enabled=True) is HELD but **not called** during a
    dry-run; the plan is still built deterministically from the marker. The provider
    is only ever called when `allow_real_call=True` (operator opt-in).

Plans are always deterministic from the marker in this phase (no real reasoning yet),
and the provider response is redacted before it is kept. `build_planner_from_config`
selects the provider via the fail-closed loader (fake default; real only when
`provider!=fake` AND `allow_real_api_calls=true` AND `api_key_env` set).
"""
from __future__ import annotations

import json
from pathlib import Path

from src.llm import LLMMessage, LLMRequest, build_provider, redact_text
from src.llm.config_loader import ROOT as LLM_ROOT
from src.planner.fake_planner import _BUILDERS, _noop_plan, _resolve_marker
from src.planner.types import Plan, PlannerRequest, PlannerResponse, PlanStep


class LivePlanError(Exception):
    """Raised when a real provider's output cannot be parsed into a plan structure.

    The caller turns this into a *blocked report* — it NEVER auto-repairs and NEVER
    executes anything. The message is safe to surface (no secret) but callers should
    still redact defensively.
    """


# Fixed system instruction for live plan-only generation. It constrains the model to
# emit ONLY a declarative JSON plan using safe, read-only skills — never shell/exec,
# never secrets, never execution. The plan is validated by PlanValidator afterwards;
# an invalid plan is BLOCKED, never auto-fixed.
LIVE_PLAN_SYSTEM_PROMPT = (
    "You are a planning assistant for a strictly read-only, plan-only project "
    "inspection harness. Output ONLY a single JSON object — no prose, no markdown "
    "code fences. The JSON schema is: {\"goal\": string, \"steps\": [{\"id\": string, "
    "\"skill\": string, \"inputs\": object, \"expected_outputs\": [string], "
    "\"success_criteria\": [string], \"risk_level\": \"low\"|\"medium\"|\"high\", "
    "\"requires_approval\": boolean, \"depends_on\": [string]}]}. "
    "Use ONLY safe, read-only skills such as 'inspect_project'. NEVER use shell, bash, "
    "sh, eval, exec, system, subprocess, raw_shell, or any command-execution skill, "
    "and never put a raw command in inputs. Keep every step risk_level 'low' and "
    "requires_approval false. Each step id must be unique; every depends_on entry must "
    "reference an existing step id. Include no secrets, keys, tokens, or credentials. "
    "Prefer a single 'inspect_project' step with depends_on []. The plan is NEVER "
    "executed; it only describes steps the harness could run later."
)


def _as_str_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _extract_json(text: str) -> dict:
    """Parse the first JSON object out of a model response. Raises LivePlanError if
    the text is empty or contains no parseable JSON object. Reads nothing from disk."""
    if not isinstance(text, str) or not text.strip():
        raise LivePlanError("model output is empty")
    t = text.strip()
    try:
        return json.loads(t)
    except Exception:  # noqa: BLE001
        pass
    # Fallback: the model may have wrapped the JSON in prose / code fences — take the
    # outermost {...} span and try again.
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j != -1 and j > i:
        try:
            return json.loads(t[i:j + 1])
        except Exception:  # noqa: BLE001
            raise LivePlanError("model output is not valid JSON")
    raise LivePlanError("model output is not valid JSON")


def parse_plan_from_text(text: str, goal: str) -> Plan:
    """Build a declarative Plan from a model's JSON response. Structural parsing only
    (sane defaults for missing optional fields); it does NOT 'fix' an invalid plan —
    validation is a separate, fail-closed step in the caller. Never executes anything.
    """
    data = _extract_json(text)
    if not isinstance(data, dict):
        raise LivePlanError("model output is not a JSON object")
    steps_raw = data.get("steps")
    if not isinstance(steps_raw, list):
        raise LivePlanError("model output has no 'steps' list")

    steps: list[PlanStep] = []
    for idx, s in enumerate(steps_raw):
        if not isinstance(s, dict):
            raise LivePlanError(f"step[{idx}] is not a JSON object")
        inputs = s.get("inputs")
        steps.append(PlanStep(
            id=str(s.get("id") or f"step_{idx}"),
            skill=str(s.get("skill") or ""),
            inputs=inputs if isinstance(inputs, dict) else {},
            expected_outputs=_as_str_list(s.get("expected_outputs")),
            success_criteria=_as_str_list(s.get("success_criteria")),
            # keep the model's value verbatim (do not coerce an illegal level to a
            # legal one — the validator must be able to reject it)
            risk_level=str(s.get("risk_level", "low")),
            requires_approval=bool(s.get("requires_approval", False)),
            depends_on=_as_str_list(s.get("depends_on")),
        ))

    return Plan(
        goal=str(data.get("goal") or goal),
        marker="",
        steps=steps,
        metadata={"planner": "provider_backed_live", "source": "real_provider"},
    )


class ProviderBackedPlanner:
    """Plan-only planner backed by a pluggable provider. Never executes a step."""

    planner_name = "provider_backed"

    def __init__(self, provider, *, allow_real_call: bool = False) -> None:
        self.provider = provider
        self.allow_real_call = bool(allow_real_call)

    @property
    def provider_name(self) -> str:
        return getattr(self.provider, "provider_name", "unknown")

    @property
    def real_api_enabled(self) -> bool:
        return bool(getattr(self.provider, "real_api_enabled", False))

    def plan(self, request: PlannerRequest) -> PlannerResponse:
        marker = _resolve_marker(request)
        notes: list[str] = []

        # Only call the provider when it is safe: a fake (offline) provider, OR an
        # explicit operator opt-in for a real one. Otherwise hold it and skip the
        # call entirely — no real API in a dry-run.
        if (not self.real_api_enabled) or self.allow_real_call:
            llm_request = LLMRequest(
                messages=[LLMMessage("user", f"{request.goal}\nmarker={marker}")],
                metadata={"planner": "provider_backed"},
            )
            raw_redacted = redact_text(self.provider.complete(llm_request).text)
        else:
            raw_redacted = "(real provider held; not called in dry-run — no real API)"
            notes.append("real provider held but not called (dry-run; no real API)")

        builder = _BUILDERS.get(marker)
        plan = builder(request.goal) if builder else _noop_plan(request.goal)
        if not marker:
            notes.append("no known marker — produced a noop plan")

        return PlannerResponse(
            plan=plan,
            provider=self.provider_name,
            model=getattr(self.provider, "model", ""),
            raw_response_redacted=raw_redacted,
            notes=notes,
        )

    def live_plan(self, request: PlannerRequest, *, max_tokens: int = 800) -> PlannerResponse:
        """Generate ONE *real* plan from the provider (operator opt-in), plan-only.

        Unlike `plan()` (which builds a deterministic plan from a marker), this asks
        the real provider to produce the plan as JSON, then parses it into a `Plan`.
        It is fail-closed:

          - requires a real provider (`real_api_enabled=True`) AND explicit opt-in
            (`allow_real_call=True`) — otherwise raises `LivePlanError`;
          - refuses an empty or secret-looking goal (the goal is the ONLY untrusted
            input and it is never allowed to carry a secret);
          - sends only a FIXED system instruction + the goal — never file content,
            browser/page content, or raw run traces;
          - redacts the raw response before it is kept;
          - NEVER executes the plan and NEVER auto-repairs an invalid one (the caller
            validates and blocks on failure).
        """
        if not self.real_api_enabled:
            raise LivePlanError("live_plan requires a real provider (real_api_enabled=True)")
        if not self.allow_real_call:
            raise LivePlanError(
                "live_plan requires explicit operator opt-in (allow_real_call=True)")
        goal = (request.goal or "").strip()
        if not goal:
            raise LivePlanError("empty goal (nothing to plan)")
        if redact_text(goal) != goal:
            # Never send a secret-looking goal to the provider.
            raise LivePlanError("goal contains a secret-looking value (blocked; not sent)")

        llm_request = LLMRequest(
            messages=[
                LLMMessage("system", LIVE_PLAN_SYSTEM_PROMPT),
                LLMMessage("user", goal),
            ],
            max_tokens=max_tokens,
            metadata={"planner": "provider_backed_live"},
        )
        response = self.provider.complete(llm_request)
        raw_redacted = redact_text(response.text)
        # May raise LivePlanError — the caller turns that into a blocked report.
        plan = parse_plan_from_text(response.text, goal)
        return PlannerResponse(
            plan=plan,
            provider=self.provider_name,
            model=getattr(self.provider, "model", ""),
            raw_response_redacted=raw_redacted,
            notes=["live plan generated by a real provider (plan-only; not executed)"],
        )


def build_planner_from_config(config: dict | None = None, root: Path | str = LLM_ROOT, *,
                              fake_only: bool = False,
                              allow_real_call: bool = False) -> ProviderBackedPlanner:
    """Build a provider-aware planner via the fail-closed provider loader.

    Fake is the default; a real provider is constructed only when config opts in
    (provider!=fake AND allow_real_api_calls=true AND api_key_env). On any loader
    error the caller decides (this raises LLMProviderError — fail closed). The
    returned planner does NOT call a real provider unless allow_real_call=True.
    """
    provider = build_provider(config=config, root=root, fake_only=fake_only)
    return ProviderBackedPlanner(provider, allow_real_call=allow_real_call)
