import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

CAND = Path(__file__).resolve().parents[1]
SCRIPT = CAND / "scripts" / "patch_file_and_run_tests.py"
_spec = importlib.util.spec_from_file_location("candidate_patch_v2_under_test", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

VITE = ROOT / "fixtures" / "vite_login_bug"
PY_CALC = CAND / "fixtures" / "py_calc_bug"
PLANS = CAND / "plans"

PASS_CMD = "python3 -c \"print('ok')\""


def _tmp_copy(src: Path, name: str) -> tuple[Path, Path]:
    d = Path(tempfile.mkdtemp(prefix="v2_test_"))
    work = d / name
    shutil.copytree(src, work)
    return d, work


def test_replace_text_patch_succeeds():
    d, work = _tmp_copy(VITE, "vite_login_bug")
    plan = {
        "patches": [
            {"type": "replace_text", "file": "src/App.jsx",
             "find": "const user = undefined;", "replace": 'const user = { token: "" };'},
            {"type": "replace_text", "file": "src/App.jsx",
             "find": "const token = user.token;", "replace": 'const token = user?.token ?? "";'},
        ],
    }
    r = mod.patch_and_run(str(work), test_command=PASS_CMD, plan=plan, artifacts_dir=str(d / "a"))
    assert r["patch_applied"] is True, r
    assert r["test_passed"] is True, r
    assert r["status"] == "passed", r
    diff = (d / "a" / "patch.diff").read_text()
    assert "user?.token" in diff and "user.token" in diff
    shutil.rmtree(d, ignore_errors=True)


def test_unified_diff_patch_succeeds():
    # Uses the in-candidate non-vite fixture + its real plan file (resolved by name).
    d, work = _tmp_copy(PY_CALC, "py_calc_bug")
    r = mod.patch_and_run(str(work), plans_dir=str(PLANS), artifacts_dir=str(d / "a"))
    assert r["patch_applied"] is True, r
    assert r["test_passed"] is True, r
    assert r["status"] == "passed", r
    # The fix is reflected in the emitted diff (the runner patches its own
    # sandbox, so the caller's copy is intentionally left untouched).
    diff = (d / "a" / "patch.diff").read_text()
    assert "-    return a - b" in diff and "+    return a + b" in diff, diff
    assert (work / "calc.py").read_text() == "def add(a, b):\n    return a - b\n"
    shutil.rmtree(d, ignore_errors=True)


def test_missing_target_file_fails():
    d, work = _tmp_copy(PY_CALC, "py_calc_bug")
    plan = {"test_command": PASS_CMD,
            "patches": [{"type": "replace_text", "file": "does_not_exist.py",
                         "find": "x", "replace": "y"}]}
    r = mod.patch_and_run(str(work), plan=plan, artifacts_dir=str(d / "a"))
    assert r["patch_applied"] is False, r
    assert r["test_passed"] is False, r
    assert "target_file_not_found" in (r["failure_reason"] or ""), r
    shutil.rmtree(d, ignore_errors=True)


def test_blocked_test_command_fails_safely():
    d, work = _tmp_copy(PY_CALC, "py_calc_bug")
    r = mod.patch_and_run(str(work), test_command="sudo python3 test_calc.py",
                          plans_dir=str(PLANS), artifacts_dir=str(d / "a"))
    assert r["test_passed"] is False, r
    assert "command_blocked" in (r["failure_reason"] or ""), r
    shutil.rmtree(d, ignore_errors=True)


def test_text_not_found_fails():
    d, work = _tmp_copy(PY_CALC, "py_calc_bug")
    plan = {"test_command": PASS_CMD,
            "patches": [{"type": "replace_text", "file": "calc.py",
                         "find": "NOT THERE", "replace": "y"}]}
    r = mod.patch_and_run(str(work), plan=plan, artifacts_dir=str(d / "a"))
    assert r["patch_applied"] is False
    assert "target_text_not_found" in (r["failure_reason"] or ""), r
    shutil.rmtree(d, ignore_errors=True)


def test_source_fixtures_are_not_mutated():
    # Both source fixtures must remain in their original buggy state.
    assert "const user = undefined;" in (VITE / "src" / "App.jsx").read_text()
    assert "return a - b" in (PY_CALC / "calc.py").read_text()


def test_unified_diff_applier_unit():
    src = "def add(a, b):\n    return a - b\n"
    diff = (
        "--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n"
        " def add(a, b):\n-    return a - b\n+    return a + b\n"
    )
    out = mod.apply_unified_diff(src, diff)
    assert out == "def add(a, b):\n    return a + b\n"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
