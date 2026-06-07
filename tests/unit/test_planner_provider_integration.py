"""Unit tests for the provider-aware planner (Real Provider Planner Integration v0).

Covers ProviderBackedPlanner + build_planner_from_config:
  - fake is the default (offline; real_api_enabled=False);
  - a real provider is fail-closed without opt-in, and constructed HELD under opt-in;
  - a HELD real provider is NEVER called during a dry-run (allow_real_call=False) —
    its complete() must not run, even if it would raise;
  - the planner is strictly plan-only and never executes a step;
  - plans/notes are redacted and carry no secret.

NO real API call is made: real providers are exercised only via a recording stub
that asserts it is never invoked, and the loader never reads an env-var VALUE.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.llm.types import LLMProviderError, LLMResponse, LLMUsage
from src.planner.provider_planner import ProviderBackedPlanner, build_planner_from_config
from src.planner.plan_validator import validate_plan
from src.planner.types import PlannerRequest

PROVIDER_SRC = (ROOT / "src" / "planner" / "provider_planner.py").read_text(encoding="utf-8")
FAKE_KEY = "sk-" + "p" * 44


class _RealStub:
    """Stands in for a real provider: real_api_enabled=True, and complete() must
    NOT be called in a dry-run. If it is called, the test fails loudly."""

    provider_name = "openai"
    real_api_enabled = True
    model = "stub-model"

    def __init__(self):
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        raise AssertionError("real provider complete() must NOT be called in a dry-run")


class _CallableStub(_RealStub):
    """Like _RealStub but returns a redactable response when explicitly allowed."""

    def complete(self, request):
        self.calls += 1
        return LLMResponse(text=f"opted-in answer (key {FAKE_KEY})", provider="openai",
                           model="stub-model",
                           usage=LLMUsage(input_chars=1, output_chars=1, estimated_tokens=1),
                           redacted=True, metadata={})


def test_fake_is_default_and_offline():
    planner = build_planner_from_config(config={"llm": {"provider": "fake"}}, root=ROOT)
    assert isinstance(planner, ProviderBackedPlanner)
    assert planner.provider_name == "fake"
    assert planner.real_api_enabled is False


def test_fake_plan_is_valid_and_plan_only():
    planner = build_planner_from_config(config={"llm": {"provider": "fake"}}, root=ROOT)
    resp = planner.plan(PlannerRequest(marker="FAKE_PLAN_FULL_BROWSER_E2E"))
    assert validate_plan(resp.plan).valid is True
    assert resp.plan.steps  # a plan was produced
    assert resp.provider == "fake"


def test_real_provider_blocked_without_opt_in():
    try:
        build_planner_from_config(
            config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                            "allow_real_api_calls": False}}, root=ROOT)
        assert False, "real provider must fail closed without opt-in"
    except LLMProviderError as exc:
        assert "real_api_not_allowed" in str(exc)


def test_real_provider_constructed_held_under_opt_in():
    planner = build_planner_from_config(
        config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                        "allow_real_api_calls": True}}, root=ROOT, allow_real_call=False)
    assert planner.provider_name == "openai"
    assert planner.real_api_enabled is True
    assert planner.allow_real_call is False


def test_held_real_provider_is_never_called_in_dry_run():
    stub = _RealStub()
    planner = ProviderBackedPlanner(stub, allow_real_call=False)
    resp = planner.plan(PlannerRequest(marker="FAKE_PLAN_FULL_BROWSER_E2E"))
    # complete() raises if called; reaching here proves it was held, not called.
    assert stub.calls == 0
    assert "not called" in resp.raw_response_redacted
    assert any("not called" in n for n in resp.notes)
    # a deterministic plan is still produced from the marker
    assert validate_plan(resp.plan).valid is True


def test_opt_in_call_is_redacted_and_does_not_leak():
    stub = _CallableStub()
    planner = ProviderBackedPlanner(stub, allow_real_call=True)  # explicit operator opt-in
    resp = planner.plan(PlannerRequest(marker="FAKE_PLAN_FULL_BROWSER_E2E"))
    assert stub.calls == 1  # opt-in path DID call the provider
    assert FAKE_KEY not in resp.raw_response_redacted  # redacted
    assert "***REDACTED***" in resp.raw_response_redacted
    assert validate_plan(resp.plan).valid is True  # still plan-only


def test_fake_planner_path_never_calls_real_even_with_key_in_env():
    os.environ["OPENAI_API_KEY"] = FAKE_KEY
    try:
        planner = build_planner_from_config(config={"llm": {"provider": "fake"}}, root=ROOT)
        resp = planner.plan(PlannerRequest(marker="FAKE_PLAN_INSPECT_PROJECT"))
        assert FAKE_KEY not in resp.raw_response_redacted
        assert planner.real_api_enabled is False
    finally:
        os.environ.pop("OPENAI_API_KEY", None)


def test_source_does_not_read_env_value_or_secret_files():
    # The planner never reads an env-var VALUE or a secret file; the provider reads
    # its key only at call time (and we never call it in a dry-run).
    assert "os.environ" not in PROVIDER_SRC and "getenv" not in PROVIDER_SRC
    assert "password_and_api" not in PROVIDER_SRC
    assert "open(" not in PROVIDER_SRC


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
