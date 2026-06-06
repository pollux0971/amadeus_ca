import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.fake_repair_planner import (
    FakeRepairPlanner,
    MARKER_MISSING_ARTIFACT,
    MARKER_TEST_FAILED,
    MARKER_CONSOLE_ERROR,
)
from src.repair.proposal_validator import ACTION_ALLOWLIST
from src.repair.types import FailureAnalysis

PLANNER_SRC = (ROOT / "src" / "repair" / "fake_repair_planner.py").read_text(encoding="utf-8")


def _analysis(failure_type="test_failed"):
    return FailureAnalysis(run_ref="x", failure_type=failure_type, unmet_criteria=["tests_pass"])


def _propose(marker, failure_type="test_failed"):
    return FakeRepairPlanner().propose(_analysis(failure_type), marker=marker)


def test_missing_artifact_marker():
    p = _propose(MARKER_MISSING_ARTIFACT)
    assert p.marker == MARKER_MISSING_ARTIFACT
    assert "update_eval" in p.action_types
    assert p.applied is False


def test_test_failed_marker():
    p = _propose(MARKER_TEST_FAILED)
    assert p.marker == MARKER_TEST_FAILED
    assert "update_candidate" in p.action_types


def test_console_error_marker():
    p = _propose(MARKER_CONSOLE_ERROR)
    assert p.marker == MARKER_CONSOLE_ERROR
    assert "update_candidate" in p.action_types


def test_noop_fallback_unknown():
    p = FakeRepairPlanner().propose(_analysis(failure_type="unknown"), marker="")
    assert p.marker == ""
    assert p.action_types == ["noop"]


def test_marker_inferred_from_failure_type():
    # no explicit marker -> inferred from failure_type
    p = FakeRepairPlanner().propose(_analysis(failure_type="console_error"), marker="")
    assert p.marker == MARKER_CONSOLE_ERROR


def test_deterministic_output():
    a = _propose(MARKER_TEST_FAILED).to_dict()
    b = _propose(MARKER_TEST_FAILED).to_dict()
    assert a == b


def test_all_actions_allowlisted_and_no_shell():
    for m in (MARKER_MISSING_ARTIFACT, MARKER_TEST_FAILED, MARKER_CONSOLE_ERROR):
        p = _propose(m)
        for a in p.actions:
            assert a.action_type in ACTION_ALLOWLIST, a.action_type
    # source never emits a raw shell command / destructive action
    for bad in ("raw_shell", "subprocess", "os.system", "rm -rf", "delete_file"):
        assert bad not in PLANNER_SRC, bad


def test_planner_refuses_real_provider():
    class _Real:
        provider_name = "openai"
        real_api_enabled = True

    try:
        FakeRepairPlanner(provider=_Real())
        assert False
    except ValueError:
        pass


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
