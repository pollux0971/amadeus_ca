import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.planner.fake_planner import (
    FakePlanner,
    MARKER_FULL_BROWSER,
    MARKER_INSPECT,
    MARKER_PATCH_ONLY,
)
from src.planner.types import PlannerRequest

PLANNER_SRC = (ROOT / "src" / "planner" / "fake_planner.py").read_text(encoding="utf-8")


def _plan(marker="", goal=""):
    return FakePlanner().plan(PlannerRequest(goal=goal, marker=marker)).plan


def test_inspect_project_marker():
    plan = _plan(MARKER_INSPECT)
    assert plan.marker == MARKER_INSPECT
    assert plan.skills == ["inspect_project"]


def test_full_browser_marker():
    plan = _plan(MARKER_FULL_BROWSER)
    assert plan.marker == MARKER_FULL_BROWSER
    skills = plan.skills
    for expected in ("start_local_server", "open_localhost_browser",
                     "read_browser_console", "patch_file_and_run_tests"):
        assert expected in skills, expected
    # post-patch reverify: an open_localhost_browser AFTER the patch step
    patch_idx = skills.index("patch_file_and_run_tests")
    assert "open_localhost_browser" in skills[patch_idx + 1:]
    # depends_on forms a valid chain (every dep exists)
    ids = {s.id for s in plan.steps}
    for s in plan.steps:
        for d in s.depends_on:
            assert d in ids


def test_patch_only_marker():
    plan = _plan(MARKER_PATCH_ONLY)
    assert plan.marker == MARKER_PATCH_ONLY
    assert "patch_file_and_run_tests" in plan.skills
    assert "open_localhost_browser" not in plan.skills


def test_noop_fallback():
    plan = _plan(goal="just do something unspecified")
    assert plan.marker == ""
    assert plan.skills == ["noop"]


def test_marker_detected_from_goal():
    # marker embedded in the goal (no explicit marker arg)
    plan = _plan(goal=f"please run {MARKER_FULL_BROWSER} now")
    assert plan.marker == MARKER_FULL_BROWSER


def test_deterministic_output():
    a = _plan(MARKER_FULL_BROWSER, goal="g").to_dict()
    b = _plan(MARKER_FULL_BROWSER, goal="g").to_dict()
    assert a == b


def test_provider_is_fake_no_network_no_env():
    resp = FakePlanner().plan(PlannerRequest(goal="g", marker=MARKER_INSPECT))
    assert resp.provider == "fake"
    # the planner exercises only the fake provider; its source reads no env/network
    for needle in ("os.environ", "getenv", "socket", "urllib", "requests",
                   "http.client", "httpx"):
        assert needle not in PLANNER_SRC, needle


def test_planner_refuses_real_provider():
    class _Real:
        provider_name = "openai"
        real_api_enabled = True

    try:
        FakePlanner(provider=_Real())
        assert False, "should refuse a real_api_enabled provider"
    except ValueError:
        pass


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
