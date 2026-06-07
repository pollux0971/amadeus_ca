import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DP = ROOT / "demo_package"
REPORT = ROOT / "reports" / "demo_package_v0" / "README.md"

DOC_FILES = [
    "README.md", "01_project_overview.md", "02_architecture_summary.md",
    "03_demo_commands.md", "04_dashboard_demo.md", "05_phase_timeline.md",
    "06_safety_boundaries.md", "07_next_steps.md", "08_teacher_presentation_outline.md",
]


def test_all_demo_docs_exist():
    for f in DOC_FILES:
        assert (DP / f).exists(), f
    assert REPORT.exists()


def test_readme_is_single_entry_linking_all():
    readme = (DP / "README.md").read_text(encoding="utf-8")
    for f in DOC_FILES[1:]:
        assert f in readme, f"demo_package/README.md missing link to {f}"


def test_boundary_statements_present():
    combined = ""
    for f in DOC_FILES:
        combined += (DP / f).read_text(encoding="utf-8").lower() + "\n"
    for phrase in ("read-only dashboard", "no real api", "password_and_api.txt",
                   "no raw shell", "no stable modification", "bounded story",
                   "browser content cannot trigger tool / repair / promotion"):
        assert phrase in combined, f"missing boundary phrase: {phrase!r}"
    assert "stable promotion" in combined and ("blocked" in combined or "not started" in combined)


def test_overview_describes_the_project():
    ov = (DP / "01_project_overview.md").read_text(encoding="utf-8").lower()
    assert "harness" in ov
    assert "browser" in ov and "agent" in ov
    assert "fake" in ov and "provider" in ov


def test_demo_commands_safe_only():
    low = (DP / "03_demo_commands.md").read_text(encoding="utf-8").lower()
    # the safe commands are present
    for cmd in ("validate_workflows.py", "run_demo.py --demo vite_login_bug",
                "run_full_browser_gate.py --dry-run", "run_dashboard_smoke.py --dry-run",
                "generate_dashboard_snapshot.py", "validate_dashboard.py"):
        assert cmd in low, f"03_demo_commands.md missing safe command {cmd!r}"
    # forbidden commands must NOT appear as runnable commands
    for bad in ("llm_provider=openai", "llm_provider=anthropic", "--enable-real-api",
                "stable_promote", "promote_to_stable",
                "cat /data/python/computer_agent_v5/password_and_api.txt", "cat .env"):
        assert bad not in low, f"03_demo_commands.md contains forbidden command {bad!r}"


def test_architecture_lists_components():
    arch = (DP / "02_architecture_summary.md").read_text(encoding="utf-8").lower()
    for comp in ("provider", "planner", "execution bridge", "browser", "console",
                 "patch", "repair", "apply workspace", "candidate merge",
                 "staging", "dashboard", "evaluator"):
        assert comp in arch, f"architecture summary missing {comp!r}"


def test_timeline_covers_phases():
    tl = (DP / "05_phase_timeline.md").read_text(encoding="utf-8").lower()
    for ph in ("phase 1b", "phase 2a", "phase 3", "phase 4", "phase 5", "phase 6",
               "backlog", "dashboard"):
        assert ph in tl, f"timeline missing {ph!r}"


def test_teacher_outline_has_sections():
    out = (DP / "08_teacher_presentation_outline.md").read_text(encoding="utf-8").lower()
    for sec in ("problem", "system goal", "harness engineering", "browser e2e",
                "repair", "dashboard", "safety", "future work"):
        assert sec in out, f"teacher outline missing {sec!r}"


def test_entry_points_link_demo_package():
    assert "demo_package" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "demo_package" in (ROOT / "docs" / "quick_resume.md").read_text(encoding="utf-8")
    assert "demo_package" in (ROOT / "docs" / "next_milestone_plan.md").read_text(encoding="utf-8")
    assert "demo_package" in (ROOT / "ui_dashboard" / "README.md").read_text(encoding="utf-8")


def test_no_secret_in_demo_package():
    from src.llm.redaction import redact_text
    for f in list(DP.iterdir()) + [REPORT]:
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert redact_text(text) == text, f"secret-like content in {f}"


def test_validator_passes():
    spec = importlib.util.spec_from_file_location(
        "validate_demo_package", ROOT / "scripts" / "validate_demo_package.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check(ROOT) == [], mod.check(ROOT)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
