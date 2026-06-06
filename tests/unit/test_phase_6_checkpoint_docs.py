import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHECKPOINT = ROOT / "docs" / "checkpoints" / "checkpoint-phase-6-staging-promotion.md"
REPORT_DIR = ROOT / "reports" / "phase_6_staging_promotion"
README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"
NEXT_MILESTONE = ROOT / "docs" / "next_milestone_plan.md"
CANDIDATE_MATRIX = ROOT / "docs" / "candidate_status_matrix.md"
PROMOTION = ROOT / "docs" / "promotion_readiness_review.md"


def test_staging_promote_exists_and_workspace_only():
    sp = ROOT / "scripts" / "staging_promote.py"
    assert sp.exists()
    src = sp.read_text(encoding="utf-8")
    assert "shell=True" not in src
    assert "os.system" not in src
    assert "--approved" in src and "--reviewer" in src


def test_checkpoint_doc_exists_and_locks_key_facts():
    assert CHECKPOINT.exists()
    low = CHECKPOINT.read_text(encoding="utf-8").lower()
    for needle in (
        "checkpoint-phase-6-staging-promotion",
        "78ecae3",
        "staging promotion v0 exists",
        "staging_promote.py",
        "human-reviewed only",
        "staging-workspace-only",
        "no active candidate modification",
        "no stable modification",
        "no safety_gate modification",
        "no promotion_policy modification",
        "no auto promotion",
        "no stable promotion",
        "staged_changes",
        "rollback_verification.md",
        "stable_promotion_checklist.md",
        "fixed test command allowlist",
        "fake_staging_promotion",
        "fake_candidate_merge",
        "planner execution",
        "secret hygiene",
    ):
        assert needle in low, f"checkpoint missing: {needle!r}"


def test_report_pack_complete():
    for rel in ("README.md", "02_demo_script_staging_promotion.md",
                "03_architecture_diagram_staging_promotion.md"):
        assert (REPORT_DIR / rel).exists(), rel
    readme = (REPORT_DIR / "README.md").read_text(encoding="utf-8").lower()
    for needle in ("fake_staging_promotion", "fake_candidate_merge", "planner execution",
                   "rollback_verification.md", "stable_promotion_checklist.md",
                   "stable files modified", "no stable promotion", "no real api",
                   "deterministic fake repair"):
        assert needle in readme, f"report README missing: {needle!r}"
    demo = (REPORT_DIR / "02_demo_script_staging_promotion.md").read_text(encoding="utf-8").lower()
    for needle in ("staging_promote.py", "--approved", "--reviewer", "--dry-run",
                   "fake_staging_promotion.yaml", "staging-workspace-only",
                   "staged_changes", "rollback verification", "stable promotion checklist",
                   "no active candidate", "no stable promotion"):
        assert needle in demo, f"demo doc missing: {needle!r}"
    arch = (REPORT_DIR / "03_architecture_diagram_staging_promotion.md").read_text(encoding="utf-8").lower()
    for needle in ("stagingvalidator", "stagingpromotion", "staging promotion workspace",
                   "staged_changes", "rollback_verification", "stable_promotion_checklist",
                   "human review", "not implemented"):
        assert needle in arch, f"arch doc missing: {needle!r}"


def test_readme_links_phase_6_and_states_status():
    text = README.read_text(encoding="utf-8")
    low = text.lower()
    assert "checkpoint-phase-6-staging-promotion" in text
    assert "reports/phase_6_staging_promotion/README.md" in text
    assert "staging promotion v0 is staging-workspace-only" in low
    assert "stable promotion not started" in low


def test_quick_resume_phase_6_and_decision_point():
    low = QUICK_RESUME.read_text(encoding="utf-8").lower()
    assert "checkpoint-phase-6-staging-promotion" in low
    assert "fake_staging_promotion" in low
    assert "staging-workspace-only" in low
    assert "rollback verification generated" in low
    assert "stable promotion checklist generated" in low
    assert "stable promotion not started" in low
    assert "real provider implementation" in low
    assert "ui dashboard" in low


def test_next_milestone_marks_phase_6_complete_with_gate():
    low = NEXT_MILESTONE.read_text(encoding="utf-8").lower()
    assert "phase 6" in low and "complete and frozen" in low
    assert "stable promotion" in low
    # durable invariants
    assert "must not modify stable directly" in low or "must not modify stable" in low
    assert "rollback" in low
    assert "promotion policy" in low


def test_status_docs_staging_status():
    matrix = CANDIDATE_MATRIX.read_text(encoding="utf-8").lower()
    assert "stagingpromotion v0" in matrix
    assert "staging-workspace-only completed" in matrix
    assert "stablepromotion" in matrix and "not started" in matrix
    assert "autopromotion" in matrix and "forbidden" in matrix
    assert "stablemodification" in matrix and "forbidden" in matrix
    promo = PROMOTION.read_text(encoding="utf-8").lower()
    assert "staging promotion" in promo
    assert "stable promotion is not started" in promo
    assert "not authorize" in promo


def test_no_doc_claims_stable_promotion_completed():
    for doc in (README, QUICK_RESUME, NEXT_MILESTONE, CANDIDATE_MATRIX, PROMOTION, CHECKPOINT):
        low = doc.read_text(encoding="utf-8").lower()
        for bad in ("stable promotion completed", "stable promotion is complete",
                    "stable promotion done"):
            assert bad not in low, f"{doc.name} falsely claims {bad!r}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
