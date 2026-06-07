import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "scripts" / "openai_planner_live_plan.py"
SCRIPT_SRC = SCRIPT.read_text(encoding="utf-8")
EVAL = ROOT / "evals" / "planner" / "openai_live_plan_only_blocked_or_passed.yaml"
FIXED_GOAL = "Create a safe read-only project status inspection plan. Do not execute anything."
FAKE_KEY = "sk-" + "d" * 44

from src.planner.provider_planner import (  # noqa: E402
    LivePlanError, ProviderBackedPlanner, parse_plan_from_text,
)
from src.planner.plan_validator import validate_plan  # noqa: E402
from src.planner.types import PlannerRequest  # noqa: E402


def _run(args, env=None):
    with tempfile.TemporaryDirectory() as tmp:
        full = [*args, "--output", tmp]
        r = subprocess.run([sys.executable, str(SCRIPT), *full], capture_output=True,
                           text=True, cwd=str(ROOT), env=env)
        reports = {}
        jp = Path(tmp) / "planner_live_report.json"
        if jp.exists():
            reports["report_text"] = jp.read_text(encoding="utf-8")
            reports["report"] = json.loads(reports["report_text"])
        for name in ("plan.json", "plan_summary.md", "blocked_report.md"):
            p = Path(tmp) / name
            if p.exists():
                reports[name] = p.read_text(encoding="utf-8")
    return r, reports


def _env_without_key():
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


# ----- a stub real provider so we can exercise live_plan() WITHOUT a network call ---
class _StubProvider:
    provider_name = "openai"
    real_api_enabled = True
    model = "stub-model"

    def __init__(self, text):
        self._text = text
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        from src.llm.types import LLMResponse, LLMUsage
        return LLMResponse(text=self._text, provider="openai", model=self.model,
                           usage=LLMUsage(), redacted=True)


def test_script_and_eval_exist():
    assert SCRIPT.exists()
    assert EVAL.exists()


def test_dry_run_makes_no_api_call():
    r, reports = _run(["--goal", FIXED_GOAL, "--dry-run"], env=_env_without_key())
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["mode"] == "dry-run"
    assert data["real_api_called"] is False
    assert data["plan_executed"] is False
    assert data["auto_repair"] is False
    assert data["schema_ok"] is True and data["redaction_ok"] is True
    assert data["status"] == "DRY-RUN OK"
    assert "no_plan_yet" not in r.stdout  # sanity
    assert reports["report"]["real_api_called"] is False
    assert "plan.json" not in reports  # no plan generated in dry-run


def test_default_is_dry_run_no_call():
    # No --dry-run and no --real-call => still no real call.
    r, _ = _run(["--goal", FIXED_GOAL], env=_env_without_key())
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["real_api_called"] is False


def test_real_call_blocked_without_key():
    r, reports = _run(["--goal", FIXED_GOAL, "--real-call"], env=_env_without_key())
    assert r.returncode == 2, r.stderr
    assert "blocked" in r.stderr.lower()
    assert json.loads(r.stdout)["status"] == "BLOCKED"
    assert reports["report"]["real_api_called"] is False


def test_no_secret_in_output_even_with_key_in_env():
    env = _env_without_key()
    env["OPENAI_API_KEY"] = FAKE_KEY
    r, reports = _run(["--goal", FIXED_GOAL, "--dry-run"], env=env)
    assert r.returncode == 0, r.stderr
    assert FAKE_KEY not in r.stdout and FAKE_KEY not in r.stderr
    assert FAKE_KEY not in reports["report_text"]
    assert json.loads(r.stdout)["env_var_present"] is True  # boolean only


# ---- live_plan() unit behavior (no network; stub provider) ----
def test_live_plan_requires_real_provider_and_opt_in():
    from src.llm.fake_provider import FakeLLMProvider
    # fake provider (real_api_enabled False) -> refused
    p = ProviderBackedPlanner(FakeLLMProvider(), allow_real_call=True)
    try:
        p.live_plan(PlannerRequest(goal=FIXED_GOAL))
        assert False, "expected LivePlanError"
    except LivePlanError:
        pass
    # real provider but no opt-in -> refused, never calls complete()
    stub = _StubProvider('{"steps": []}')
    p2 = ProviderBackedPlanner(stub, allow_real_call=False)
    try:
        p2.live_plan(PlannerRequest(goal=FIXED_GOAL))
        assert False, "expected LivePlanError"
    except LivePlanError:
        pass
    assert stub.calls == 0


def test_live_plan_parses_valid_json_into_valid_plan():
    good = json.dumps({"goal": FIXED_GOAL, "steps": [{
        "id": "inspect", "skill": "inspect_project", "inputs": {},
        "expected_outputs": ["status"], "success_criteria": ["project_inspected"],
        "risk_level": "low", "requires_approval": False, "depends_on": []}]})
    planner = ProviderBackedPlanner(_StubProvider(good), allow_real_call=True)
    resp = planner.live_plan(PlannerRequest(goal=FIXED_GOAL))
    assert validate_plan(resp.plan).valid is True
    assert resp.plan.skills == ["inspect_project"]


def test_live_plan_non_json_raises():
    planner = ProviderBackedPlanner(_StubProvider("sorry, here is some prose"),
                                    allow_real_call=True)
    try:
        planner.live_plan(PlannerRequest(goal=FIXED_GOAL))
        assert False, "expected LivePlanError"
    except LivePlanError:
        pass


def test_live_plan_secret_goal_refused_and_not_sent():
    stub = _StubProvider('{"steps": []}')
    planner = ProviderBackedPlanner(stub, allow_real_call=True)
    secret_goal = "inspect using sk-" + "a" * 40
    try:
        planner.live_plan(PlannerRequest(goal=secret_goal))
        assert False, "expected LivePlanError"
    except LivePlanError:
        pass
    assert stub.calls == 0  # secret-looking goal never sent


def test_invalid_plan_from_parser_is_caught_by_validator():
    bad = json.dumps({"steps": [{"id": "x", "skill": "raw_shell"}]})
    plan = parse_plan_from_text(bad, FIXED_GOAL)
    assert validate_plan(plan).valid is False  # forbidden skill -> blocked, not fixed


def test_script_safety_invariants_in_source():
    assert "--real-call" in SCRIPT_SRC and "--dry-run" in SCRIPT_SRC
    assert "fail closed" in SCRIPT_SRC.lower() or "fail-closed" in SCRIPT_SRC.lower()
    # the key is only ever read from the named env var; never opens a secret file
    assert "os.environ.get(API_KEY_ENV)" in SCRIPT_SRC
    assert "open(" not in SCRIPT_SRC
    # plan-only: the script must never import an executor / repair / promotion runtime
    for forbidden in ("execution_bridge", "src.repair", "staging_promote", "execute_plan"):
        assert forbidden not in SCRIPT_SRC, forbidden
    assert "redact" in SCRIPT_SRC


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
