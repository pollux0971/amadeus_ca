import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHECKPOINT = ROOT / "docs" / "checkpoints" / "checkpoint-phase-2a-fake-planner-execution.md"
REPORT_DIR = ROOT / "reports" / "phase_2_fake_planner_execution"
README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"
NEXT_MILESTONE = ROOT / "docs" / "next_milestone_plan.md"
CANDIDATE_MATRIX = ROOT / "docs" / "candidate_status_matrix.md"
PROMOTION = ROOT / "docs" / "promotion_readiness_review.md"


def test_checkpoint_doc_exists_and_locks_key_facts():
    assert CHECKPOINT.exists()
    low = CHECKPOINT.read_text(encoding="utf-8").lower()
    for needle in (
        "checkpoint-phase-2a-fake-planner-execution",
        "f6e71b0",                       # frozen commit
        "fake provider only",
        "deterministic",
        "plan-only",
        "only accepts a validated plan",
        "allowlisted skills",
        "no direct shell",
        "no autonomous replan",
        "high-risk requires approval",
        "fake_patch_plan_execution",
        "fake_full_browser_plan_execution",
        "full_browser_vite_login_bug_e2e",
        "secret hygiene",
        "untouched",
        "auto repair loop",
    ):
        assert needle in low, f"checkpoint missing: {needle!r}"


def test_report_pack_complete():
    for rel in ("README.md", "02_demo_script_planner_execution.md",
                "03_architecture_diagram_planner_execution.md"):
        assert (REPORT_DIR / rel).exists(), rel
    readme = (REPORT_DIR / "README.md").read_text(encoding="utf-8").lower()
    # results table + remaining risks
    for needle in ("fake_full_browser_plan", "fake_patch_plan_execution",
                   "fake_full_browser_plan_execution", "remaining risks",
                   "no real api", "no auto-repair", "no autonomous replan",
                   "deterministic", "human review"):
        assert needle in readme, f"report README missing: {needle!r}"
    demo = (REPORT_DIR / "02_demo_script_planner_execution.md").read_text(encoding="utf-8").lower()
    for needle in ("plan_task.py", "execute_plan.py",
                   "fake_full_browser_plan_execution.yaml", "no direct shell",
                   "allowlisted skills", "no autonomous replan", "fake provider"):
        assert needle in demo, f"demo doc missing: {needle!r}"
    arch = (REPORT_DIR / "03_architecture_diagram_planner_execution.md").read_text(encoding="utf-8").lower()
    for needle in ("fakellmprovider", "fakeplanner", "planvalidator",
                   "executionbridge", "orchestrator", "skillexecutor", "evaluator"):
        assert needle in arch, f"arch doc missing: {needle!r}"


def test_readme_links_phase_2a_and_states_status():
    text = README.read_text(encoding="utf-8")
    low = text.lower()
    assert "checkpoint-phase-2a-fake-planner-execution" in text
    assert "reports/phase_2_fake_planner_execution/README.md" in text
    assert "fake planner execution bridge is green" in low
    assert "auto-repair is not started" in low


def test_quick_resume_phase_2a_and_decision_point():
    low = QUICK_RESUME.read_text(encoding="utf-8").lower()
    assert "checkpoint-phase-2a-fake-planner-execution" in low
    assert "fake_full_browser_plan_execution" in low
    assert "fake_patch_plan_execution" in low
    # decision point with the four options + auto-repair not started
    assert "auto repair loop" in low
    assert "auto-repair is not started" in low or "auto-repair not started" in low
    assert "real provider implementation" in low
    assert "ui dashboard" in low


def test_next_milestone_marks_phase_2a_complete_with_gate():
    low = NEXT_MILESTONE.read_text(encoding="utf-8").lower()
    assert "phase 2a is complete" in low
    assert "auto repair loop" in low
    # auto-repair gate prerequisites
    assert "repair proposal only" in low
    assert "candidate workspace" in low
    assert "approval gate" in low
    assert "must not modify stable directly" in low


def test_status_docs_mention_autorepair_not_started():
    matrix = CANDIDATE_MATRIX.read_text(encoding="utf-8").lower()
    assert "autorepairloop" in matrix
    assert "not started" in matrix
    assert "executionbridge v1" in matrix
    promo = PROMOTION.read_text(encoding="utf-8").lower()
    assert "auto-repair" in promo and "not started" in promo
    assert "not a stable promotion" in promo or "not a promotion" in promo


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
