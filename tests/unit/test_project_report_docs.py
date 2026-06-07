import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PR = ROOT / "project_report"

SECTIONS = [
    "README.md", "01_abstract.md", "02_motivation_and_problem.md",
    "03_system_architecture.md", "04_harness_engineering_method.md",
    "05_implementation_phases.md", "06_evaluation_and_results.md",
    "07_safety_and_risk_management.md", "08_demo_and_dashboard.md",
    "09_limitations.md", "10_future_work.md", "11_conclusion.md",
    "12_presentation_script.md",
]


def test_all_sections_exist():
    for f in SECTIONS:
        assert (PR / f).exists(), f
    assert (ROOT / "reports" / "project_report_v1" / "README.md").exists()


def test_architecture_has_diagram():
    arch = (PR / "03_system_architecture.md").read_text(encoding="utf-8").lower()
    assert "```mermaid" in arch or "flowchart" in arch
    for comp in ("provider", "planner", "execution bridge", "dashboard", "staging"):
        assert comp in arch, f"architecture missing {comp!r}"


def test_phase_timeline_present():
    tl = (PR / "05_implementation_phases.md").read_text(encoding="utf-8").lower()
    assert "phase timeline" in tl
    for ph in ("phase 1b", "phase 2a", "phase 3", "phase 4", "phase 5", "phase 6"):
        assert ph in tl, f"timeline missing {ph!r}"


def test_evaluation_results_table():
    res = (PR / "06_evaluation_and_results.md").read_text(encoding="utf-8").lower()
    assert "results table" in res
    assert "453" in res            # unit tests count
    assert "1.0" in res            # eval scores
    assert "no-go" in res or "blocked" in res  # stable audit result


def test_safety_section_lists_boundaries():
    s = (PR / "07_safety_and_risk_management.md").read_text(encoding="utf-8").lower()
    for phrase in ("no real api", "no raw shell", "no stable modification",
                   "no safety_gate modification", "no promotion_policy modification",
                   "browser content cannot trigger tool / repair / promotion",
                   "password_and_api.txt"):
        assert phrase in s, f"safety section missing {phrase!r}"


def test_future_work_covers_all_epics():
    fw = (PR / "10_future_work.md").read_text(encoding="utf-8").lower()
    for item in ("stable promotion", "ui", "real provider", "multimodal"):
        assert item in fw, f"future work missing {item!r}"
    assert "human review" in fw


def test_presentation_script_is_timed():
    sc = (PR / "12_presentation_script.md").read_text(encoding="utf-8").lower()
    assert "presentation script" in sc
    assert "[0:00" in sc
    assert "thank you" in sc


def test_stable_audit_recorded_as_no_go():
    combined = "\n".join((PR / f).read_text(encoding="utf-8").lower() for f in SECTIONS)
    assert "no-go" in combined or "blocked" in combined
    for bad in ("stable promotion completed", "stable promotion is complete",
                "stable promotion done", "promoted to stable"):
        assert bad not in combined, f"report falsely claims {bad!r}"


def test_describes_the_project():
    combined = "\n".join((PR / f).read_text(encoding="utf-8").lower() for f in SECTIONS)
    for phrase in ("harness engineering", "browser", "fake provider", "repair proposal",
                   "candidate merge", "staging", "demo package"):
        assert phrase in combined, f"report missing {phrase!r}"


def test_entry_points_link_report():
    for doc in ("README.md", "docs/quick_resume.md", "demo_package/README.md",
                "docs/next_milestone_plan.md"):
        assert "project_report" in (ROOT / doc).read_text(encoding="utf-8"), doc


def test_no_secret_in_report():
    from src.llm.redaction import redact_text
    for f in list(PR.iterdir()) + [ROOT / "reports" / "project_report_v1" / "README.md"]:
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert redact_text(text) == text, f"secret-like content in {f}"


def test_validator_passes():
    spec = importlib.util.spec_from_file_location(
        "validate_project_report", ROOT / "scripts" / "validate_project_report.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check(ROOT) == [], mod.check(ROOT)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
