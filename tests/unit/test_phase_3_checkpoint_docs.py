import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHECKPOINT = ROOT / "docs" / "checkpoints" / "checkpoint-phase-3-repair-proposal-only.md"
REPORT_DIR = ROOT / "reports" / "phase_3_repair_proposal_only"
README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"
NEXT_MILESTONE = ROOT / "docs" / "next_milestone_plan.md"
CANDIDATE_MATRIX = ROOT / "docs" / "candidate_status_matrix.md"
PROMOTION = ROOT / "docs" / "promotion_readiness_review.md"


def test_no_repair_apply_script():
    assert not (ROOT / "scripts" / "repair_apply.py").exists()


def test_checkpoint_doc_exists_and_locks_key_facts():
    assert CHECKPOINT.exists()
    low = CHECKPOINT.read_text(encoding="utf-8").lower()
    for needle in (
        "checkpoint-phase-3-repair-proposal-only",
        "b1ffd56",
        "repair loop v0 exists",
        "proposal-only",
        "no apply",
        "repair_apply.py",
        "no auto promotion",
        "redacted artifact metadata",
        "fake repair planner only",
        "modify_stable_skill",
        "modify_safety_gate",
        "modify_promotion_policy",
        "raw_shell",
        "delete_file",
        "applied=true",
        "candidate workspace created",
        "fake_repair_proposal_only",
        "--apply",
        "rejected",
        "secret hygiene",
        "untouched",
        "approved patch application",
    ):
        assert needle in low, f"checkpoint missing: {needle!r}"


def test_report_pack_complete():
    for rel in ("README.md", "02_demo_script_repair_proposal.md",
                "03_architecture_diagram_repair_proposal.md"):
        assert (REPORT_DIR / rel).exists(), rel
    readme = (REPORT_DIR / "README.md").read_text(encoding="utf-8").lower()
    for needle in ("fake_repair_proposal_only", "--apply", "rejected",
                   "no stable files modified", "no secret in proposal",
                   "no approved apply", "no auto promotion", "no real api",
                   "deterministic", "human approval"):
        assert needle in readme, f"report README missing: {needle!r}"
    demo = (REPORT_DIR / "02_demo_script_repair_proposal.md").read_text(encoding="utf-8").lower()
    for needle in ("repair_propose.py", "fake_repair_proposal_only.yaml",
                   "failure analyzer", "fake repair planner", "proposal validator",
                   "candidate workspace", "not auto-repair"):
        assert needle in demo, f"demo doc missing: {needle!r}"
    arch = (REPORT_DIR / "03_architecture_diagram_repair_proposal.md").read_text(encoding="utf-8").lower()
    for needle in ("failureanalyzer", "fakerepairplanner", "proposalvalidator",
                   "candidateworkspace", "human approval gate", "not implemented"):
        assert needle in arch, f"arch doc missing: {needle!r}"


def test_readme_links_phase_3_and_states_status():
    text = README.read_text(encoding="utf-8")
    low = text.lower()
    assert "checkpoint-phase-3-repair-proposal-only" in text
    assert "reports/phase_3_repair_proposal_only/README.md" in text
    assert "auto repair loop v0 is proposal-only" in low
    assert "approved patch application is not started" in low


def test_quick_resume_phase_3_and_decision_point():
    low = QUICK_RESUME.read_text(encoding="utf-8").lower()
    assert "checkpoint-phase-3-repair-proposal-only" in low
    assert "fake_repair_proposal_only" in low
    assert "proposal-only" in low
    assert "--apply" in low and "rejected" in low
    assert "repair apply not implemented" in low
    assert "approved patch application" in low
    assert "real provider implementation" in low
    assert "ui dashboard" in low


def test_next_milestone_marks_phase_3_complete_with_gate():
    low = NEXT_MILESTONE.read_text(encoding="utf-8").lower()
    assert "phase 3" in low and "complete and frozen" in low
    assert "approved patch application" in low
    # gate prerequisites
    assert "must not modify stable directly" in low
    assert "candidate workspace" in low
    assert "human approval" in low
    assert "targeted tests + regression" in low
    assert "promotion policy" in low
    assert "rollback" in low


def test_status_docs_repair_status():
    matrix = CANDIDATE_MATRIX.read_text(encoding="utf-8").lower()
    assert "autorepairloop v0" in matrix
    assert "proposal-only completed" in matrix
    assert "repairapply" in matrix and "not started" in matrix
    assert "autopromotion" in matrix and "forbidden" in matrix
    promo = PROMOTION.read_text(encoding="utf-8").lower()
    assert "repair" in promo and "not implemented" in promo
    assert "does not authorize" in promo or "not authorize" in promo


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
