import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHECKPOINT = ROOT / "docs" / "checkpoints" / "checkpoint-phase-5-candidate-merge.md"
REPORT_DIR = ROOT / "reports" / "phase_5_candidate_merge"
README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"
NEXT_MILESTONE = ROOT / "docs" / "next_milestone_plan.md"
CANDIDATE_MATRIX = ROOT / "docs" / "candidate_status_matrix.md"
PROMOTION = ROOT / "docs" / "promotion_readiness_review.md"


def test_repair_merge_exists_and_workspace_only():
    rm = ROOT / "scripts" / "repair_merge.py"
    assert rm.exists()
    src = rm.read_text(encoding="utf-8")
    assert "shell=True" not in src
    assert "os.system" not in src
    assert "--approved" in src and "--reviewer" in src


def test_checkpoint_doc_exists_and_locks_key_facts():
    assert CHECKPOINT.exists()
    low = CHECKPOINT.read_text(encoding="utf-8").lower()
    for needle in (
        "checkpoint-phase-5-candidate-merge",
        "b5ee165",
        "candidate merge v0 exists",
        "repair_merge.py",
        "human-reviewed only",
        "candidate-workspace-only merge",
        "no active candidate modification",
        "no stable modification",
        "no safety_gate modification",
        "no promotion_policy modification",
        "no auto promotion",
        "no staging promotion",
        "no stable promotion",
        "merged_changes",
        "rollback_plan.md",
        "promotion_review_package.md",
        "fixed test command allowlist",
        "fake_candidate_merge",
        "fake_approved_patch_application",
        "planner execution",
        "secret hygiene",
    ):
        assert needle in low, f"checkpoint missing: {needle!r}"


def test_report_pack_complete():
    for rel in ("README.md", "02_demo_script_candidate_merge.md",
                "03_architecture_diagram_candidate_merge.md"):
        assert (REPORT_DIR / rel).exists(), rel
    readme = (REPORT_DIR / "README.md").read_text(encoding="utf-8").lower()
    for needle in ("fake_candidate_merge", "fake_approved_patch_application",
                   "planner execution", "rollback_plan.md", "promotion_review_package.md",
                   "stable files modified", "no auto promotion", "no staging promotion",
                   "no stable promotion", "no real api", "deterministic fake repair"):
        assert needle in readme, f"report README missing: {needle!r}"
    demo = (REPORT_DIR / "02_demo_script_candidate_merge.md").read_text(encoding="utf-8").lower()
    for needle in ("repair_merge.py", "--approved", "--reviewer", "--dry-run",
                   "fake_candidate_merge.yaml", "candidate-workspace-only",
                   "merged_changes", "rollback plan", "promotion review package",
                   "no active candidate", "no stable promotion"):
        assert needle in demo, f"demo doc missing: {needle!r}"
    arch = (REPORT_DIR / "03_architecture_diagram_candidate_merge.md").read_text(encoding="utf-8").lower()
    for needle in ("mergevalidator", "candidatemerge", "candidate merge workspace",
                   "merged_changes", "rollback_plan", "promotion_review_package",
                   "human review", "not implemented"):
        assert needle in arch, f"arch doc missing: {needle!r}"


def test_readme_links_phase_5_and_states_status():
    text = README.read_text(encoding="utf-8")
    low = text.lower()
    assert "checkpoint-phase-5-candidate-merge" in text
    assert "reports/phase_5_candidate_merge/README.md" in text
    assert "candidate merge v0 is candidate-workspace-only" in low
    assert "staging / stable promotion not started" in low


def test_quick_resume_phase_5_and_decision_point():
    low = QUICK_RESUME.read_text(encoding="utf-8").lower()
    assert "checkpoint-phase-5-candidate-merge" in low
    assert "fake_candidate_merge" in low
    assert "candidate-workspace-only" in low
    assert "rollback plan generated" in low
    assert "promotion review package generated" in low
    assert "staging promotion not started" in low
    assert "stable promotion not started" in low
    assert "real provider implementation" in low
    assert "ui dashboard" in low


def test_next_milestone_marks_phase_5_complete_with_gate():
    low = NEXT_MILESTONE.read_text(encoding="utf-8").lower()
    assert "phase 5" in low and "complete and frozen" in low
    assert "staging promotion" in low
    # durable invariants
    assert "must not modify stable directly" in low
    assert "verify the rollback plan" in low or "rollback plan" in low
    assert "promotion policy" in low


def test_status_docs_merge_status():
    matrix = CANDIDATE_MATRIX.read_text(encoding="utf-8").lower()
    assert "candidatemerge v0" in matrix
    assert "candidate-workspace-only completed" in matrix
    assert "stagingpromotion" in matrix and "not started" in matrix
    assert "stablepromotion" in matrix and "not started" in matrix
    assert "autopromotion" in matrix and "forbidden" in matrix
    assert "stablemodification" in matrix and "forbidden" in matrix
    promo = PROMOTION.read_text(encoding="utf-8").lower()
    assert "candidate merge" in promo
    assert "promotion is not started" in promo
    assert "not authorize" in promo


def test_no_doc_claims_promotion_completed():
    for doc in (README, QUICK_RESUME, NEXT_MILESTONE, CANDIDATE_MATRIX, PROMOTION, CHECKPOINT):
        low = doc.read_text(encoding="utf-8").lower()
        for bad in ("staging promotion completed", "staging promotion is complete",
                    "stable promotion completed", "stable promotion is complete",
                    "stable promotion done"):
            assert bad not in low, f"{doc.name} falsely claims {bad!r}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
