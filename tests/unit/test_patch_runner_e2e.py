import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.skills_runtime.simple_yaml import load_yaml
from src.orchestrator.orchestrator import Orchestrator

EVAL = ROOT / "evals" / "patch_runner" / "py_calc_bug_e2e.yaml"
FIXTURE = ROOT / "harnesses/candidates/patch_file_and_run_tests_v2/fixtures/py_calc_bug"


def _run(candidates_dir="harnesses/candidates"):
    task = load_yaml(EVAL)
    tmp = tempfile.mkdtemp(prefix="e2e_runs_")
    orch = Orchestrator(task["id"], task["user_goal"], runs_dir=tmp, candidates_dir=candidates_dir)
    run_dir = orch.run_eval_task(task, eval_path=EVAL)
    return run_dir, json.loads((run_dir / "score.json").read_text(encoding="utf-8"))


def test_e2e_passes_with_candidates_enabled():
    run_dir, score = _run()
    assert score["task_success"] is True
    assert score["score"] == 1.0
    crit = {r["criterion"]: r["passed"] for r in score["criteria_results"]}
    assert crit["source_file_patched"] is True
    assert crit["tests_pass"] is True
    # All required artifacts emitted.
    for name in ("patch.diff", "test.log", "result.json"):
        assert (run_dir / "artifacts" / name).exists(), f"missing {name}"
    assert (run_dir / "score.json").exists()
    assert (run_dir / "summary.md").exists()
    assert not (run_dir / "failure_report.md").exists()
    # The unified_diff plan really landed, and the eval's test_command was used.
    diff = (run_dir / "artifacts" / "patch.diff").read_text(encoding="utf-8")
    assert "-    return a - b" in diff and "+    return a + b" in diff
    test_log = (run_dir / "artifacts" / "test.log").read_text(encoding="utf-8")
    assert "python3 test_calc.py" in test_log


def test_e2e_does_not_misuse_v2_when_candidates_disabled():
    # With overlays off, the stable placeholder runs -> the slice must NOT pass,
    # proving v2 is not silently used.
    run_dir, score = _run(candidates_dir=None)
    assert score["task_success"] is False
    crit = {r["criterion"]: r["passed"] for r in score["criteria_results"]}
    assert crit["source_file_patched"] is False
    assert crit["tests_pass"] is False
    assert "not_implemented" in (score["failure"]["root_cause"] or "")


def test_e2e_does_not_mutate_source_fixture():
    _run()
    assert (FIXTURE / "calc.py").read_text(encoding="utf-8") == "def add(a, b):\n    return a - b\n"
    assert "from calc import add" in (FIXTURE / "test_calc.py").read_text(encoding="utf-8")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
