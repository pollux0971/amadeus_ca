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

from pathlib import Path

from src.llm import LLMMessage, LLMRequest, build_provider, redact_text
from src.llm.config_loader import ROOT as LLM_ROOT
from src.planner.fake_planner import _BUILDERS, _noop_plan, _resolve_marker
from src.planner.types import PlannerRequest, PlannerResponse


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
