from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.skills_runtime.executor import SkillExecutor, CALLABLE_ALIASES

SKILLS = ROOT / "skills"
VITE = str(ROOT / "fixtures" / "vite_login_bug")


def test_discovers_all_packaged_skills():
    ex = SkillExecutor(SKILLS)
    found = ex.available_skills()
    for skill_id in (
        "inspect_project",
        "start_local_server",
        "open_localhost_browser",
        "read_browser_console",
        "patch_file_and_run_tests",
    ):
        assert skill_id in found


def test_runs_skill_whose_function_matches_id():
    ex = SkillExecutor(SKILLS)
    result = ex.run("inspect_project", {"project_dir": VITE})
    assert result.ok
    assert result.output["project_type"] == "node"


def test_resolves_aliased_callable():
    # start_local_server's entry function is simulate_start_server, not the id.
    assert CALLABLE_ALIASES["start_local_server"] == "simulate_start_server"
    ex = SkillExecutor(SKILLS)
    result = ex.run("start_local_server", {"project_dir": VITE})
    assert result.ok
    assert result.output["status"] == "started"
    assert result.output["server_url"]


def test_binds_only_declared_inputs():
    # Extra keys must be ignored, not passed through to the function.
    ex = SkillExecutor(SKILLS)
    result = ex.run("inspect_project", {"project_dir": VITE, "unexpected": 123})
    assert result.ok
    assert "unexpected" not in result.used_inputs


def test_missing_required_input_is_reported_not_raised():
    ex = SkillExecutor(SKILLS)
    result = ex.run("inspect_project", {})
    assert not result.ok
    assert "missing required inputs" in (result.error or "")


def test_unknown_skill_is_reported_not_raised():
    ex = SkillExecutor(SKILLS)
    result = ex.run("no_such_skill", {})
    assert not result.ok
    assert "unknown skill" in (result.error or "")


def test_placeholder_skill_reports_failure_status():
    # patch_file_and_run_tests returns status=not_implemented -> ok must be False.
    ex = SkillExecutor(SKILLS)
    result = ex.run(
        "patch_file_and_run_tests",
        {"project_dir": VITE, "patch": "", "test_command": "npm test"},
    )
    assert not result.ok
    assert result.output["status"] == "not_implemented"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
