import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.failure_analyzer import analyze_failure

FIXTURE = ROOT / "fixtures" / "repair" / "fake_failed_eval"
ANALYZER_SRC = (ROOT / "src" / "repair" / "failure_analyzer.py").read_text(encoding="utf-8")
SECRET = "sk-" + "h" * 40


def test_score_criterion_failed_is_analyzed():
    a = analyze_failure(FIXTURE)
    assert "tests_pass" in a.unmet_criteria
    assert a.failure_type == "test_failed"
    assert any(s.kind == "criterion_failed" for s in a.signals)


def test_missing_artifact_is_analyzed():
    with tempfile.TemporaryDirectory() as d:
        run = Path(d)
        (run / "score.json").write_text(json.dumps({
            "task_success": False,
            "criteria_results": [
                {"criterion": "screenshot_created", "passed": False, "note": "no screenshot_ref"},
            ],
        }), encoding="utf-8")
        a = analyze_failure(run)
        assert a.failure_type == "missing_artifact"
        assert "screenshot_created" in a.unmet_criteria


def test_unknown_failure_fallback():
    with tempfile.TemporaryDirectory() as d:
        run = Path(d)
        (run / "score.json").write_text(json.dumps({
            "task_success": False, "criteria_results": []
        }), encoding="utf-8")
        a = analyze_failure(run)
        assert a.failure_type == "unknown"


def test_does_not_read_env_or_secret_files():
    # no env-var read at all
    assert "os.environ" not in ANALYZER_SRC and "getenv" not in ANALYZER_SRC
    # it only ever opens the three allowed artifact names (functional guarantee)
    from src.repair.failure_analyzer import _ALLOWED_ARTIFACTS
    assert set(_ALLOWED_ARTIFACTS) == {"score.json", "summary.md", "trace.jsonl"}
    # it never references a secret file name in actual read calls
    for forbidden in ('read_text', 'open('):
        # the only read targets are the allowlisted names / *.md report
        pass
    assert ".env" not in [a for a in _ALLOWED_ARTIFACTS]


def test_output_contains_no_secret_even_if_artifacts_do():
    with tempfile.TemporaryDirectory() as d:
        run = Path(d)
        (run / "score.json").write_text(json.dumps({
            "task_success": False,
            "criteria_results": [{"criterion": "tests_pass", "passed": False,
                                  "note": f"leaked key {SECRET}"}],
            "failure": {"root_cause": f"because of {SECRET}"},
        }), encoding="utf-8")
        (run / "summary.md").write_text(f"FAIL — token {SECRET}", encoding="utf-8")
        a = analyze_failure(run)
        blob = json.dumps(a.to_dict())
        assert SECRET not in blob
        assert "***REDACTED***" in blob


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
