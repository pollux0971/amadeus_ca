import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "patch_file_and_run_tests.py"
_spec = importlib.util.spec_from_file_location("candidate_patch_under_test", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

FIXTURE = ROOT / "fixtures" / "vite_login_bug"


def test_patch_applied_and_tests_pass():
    with tempfile.TemporaryDirectory() as d:
        work = Path(d) / "vite"
        shutil.copytree(FIXTURE, work)
        adir = Path(d) / "artifacts"
        r = mod.patch_and_run(str(work), test_command="npm test", artifacts_dir=str(adir))
        assert r["patch_applied"] is True, r
        assert r["test_passed"] is True, r
        assert r["status"] == "passed", r
        assert r["returncode"] == 0, r
        assert (adir / "patch.diff").exists()
        assert (adir / "test.log").exists()
        assert (adir / "result.json").exists()


def test_diff_contains_the_fix():
    with tempfile.TemporaryDirectory() as d:
        work = Path(d) / "vite"
        shutil.copytree(FIXTURE, work)
        adir = Path(d) / "artifacts"
        mod.patch_and_run(str(work), test_command="npm test", artifacts_dir=str(adir))
        diff = (adir / "patch.diff").read_text(encoding="utf-8")
        assert "user.token" in diff          # the removed buggy line
        assert "user?.token" in diff         # the added safe line


def test_blocked_test_command_fails_safely():
    # A command denied by the Safety Gate must fail the run, not bypass it.
    with tempfile.TemporaryDirectory() as d:
        work = Path(d) / "vite"
        shutil.copytree(FIXTURE, work)
        r = mod.patch_and_run(str(work), test_command="sudo npm test", artifacts_dir=str(Path(d) / "a"))
        assert r["test_passed"] is False
        assert "command_blocked" in (r["error"] or "")


def test_does_not_mutate_committed_fixture():
    # The real fixture must stay buggy: we only ever patch a sandbox copy.
    src = (FIXTURE / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "const user = undefined;" in src
    assert "const token = user.token;" in src


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
