from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "test_environment_baseline.md"
SCRIPT = ROOT / "scripts" / "check_test_environment_baseline.py"
VALIDATE = ROOT / "scripts" / "validate_workflows.py"


def test_baseline_doc_exists():
    assert DOC.exists()


def test_baseline_script_exists():
    assert SCRIPT.exists()


def test_doc_covers_required_topics():
    t = DOC.read_text(encoding="utf-8").lower()
    for needle in ("system python", ".venv", "playwright",
                   "regression vs environment gap", "environment gap",
                   ".venv/bin/python"):
        assert needle in t, needle


def test_doc_states_which_tests_run_where_and_dry_run_split():
    t = DOC.read_text(encoding="utf-8").lower()
    # which tests must run on .venv, and which dry-runs are safe on system python
    assert "must run on" in t and "real browser" in t
    assert "dry-run" in t
    assert "http_fallback" in t


def test_doc_lists_known_env_gap_tests():
    t = DOC.read_text(encoding="utf-8")
    assert "test_browser_keep_alive_e2e.py" in t
    assert "test_full_browser_gate_script.py::test_missing_prereqs_block_with_exit_2" in t


def test_doc_forbids_masking_new_failures_with_baseline():
    t = DOC.read_text(encoding="utf-8").lower()
    # must contain the rule that a known failing baseline cannot hide a new failure
    assert "never" in t and ("hide" in t or "mask" in t)


def test_doc_says_python_not_on_path_is_warning_only():
    t = DOC.read_text(encoding="utf-8").lower()
    assert "warning" in t and "path" in t
    # the doc must NOT require python to be on PATH
    assert "must be on path" not in t


def test_validate_workflows_wires_in_the_baseline_check():
    s = VALIDATE.read_text(encoding="utf-8")
    assert "_test_environment_baseline_errors" in s
    assert "check_test_environment_baseline" in s


def test_real_browser_path_is_venv_python():
    t = DOC.read_text(encoding="utf-8")
    assert ".venv/bin/python" in t
    # the doc names the .venv as the real-browser verification path
    assert "verification path" in t.lower()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
