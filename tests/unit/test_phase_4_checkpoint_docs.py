import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHECKPOINT = ROOT / "docs" / "checkpoints" / "checkpoint-phase-4-approved-patch-application.md"
REPORT_DIR = ROOT / "reports" / "phase_4_approved_patch_application"
README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"
NEXT_MILESTONE = ROOT / "docs" / "next_milestone_plan.md"
CANDIDATE_MATRIX = ROOT / "docs" / "candidate_status_matrix.md"
PROMOTION = ROOT / "docs" / "promotion_readiness_review.md"


def test_repair_apply_exists_and_workspace_only():
    rap = ROOT / "scripts" / "repair_apply.py"
    assert rap.exists()
    src = rap.read_text(encoding="utf-8")
    assert "shell=True" not in src
    assert "os.system" not in src
    assert "--approved" in src


def test_checkpoint_doc_exists_and_locks_key_facts():
    assert CHECKPOINT.exists()
    low = CHECKPOINT.read_text(encoding="utf-8").lower()
    for needle in (
        "checkpoint-phase-4-approved-patch-application",
        "0eca9de",
        "approved patch application v0 exists",
        "repair_apply.py",
        "human-approved only",
        "workspace-only apply",
        "no stable modification",
        "no safety_gate modification",
        "no promotion_policy modification",
        "no auto promotion",
        "no merge",
        "proposed_changes",
        "fixed test command allowlist",
        "fake_approved_patch_application",
        "fake_repair_proposal_only",
        "planner execution",
        "secret hygiene",
        "merge + promotion",
    ):
        assert needle in low, f"checkpoint missing: {needle!r}"


def test_report_pack_complete():
    for rel in ("README.md", "02_demo_script_approved_apply.md",
                "03_architecture_diagram_approved_apply.md"):
        assert (REPORT_DIR / rel).exists(), rel
    readme = (REPORT_DIR / "README.md").read_text(encoding="utf-8").lower()
    for needle in ("fake_approved_patch_application", "fake_repair_proposal_only",
                   "planner execution", "stable files modified", "no auto promotion",
                   "no merge yet", "rollback plan required", "no real api",
                   "deterministic fake repair"):
        assert needle in readme, f"report README missing: {needle!r}"
    demo = (REPORT_DIR / "02_demo_script_approved_apply.md").read_text(encoding="utf-8").lower()
    for needle in ("repair_apply.py", "--approved", "--dry-run",
                   "fake_approved_patch_application.yaml", "explicit approval",
                   "workspace-only", "proposed_changes", "fixed test allowlist",
                   "no merge", "stable untouched"):
        assert needle in demo, f"demo doc missing: {needle!r}"
    arch = (REPORT_DIR / "03_architecture_diagram_approved_apply.md").read_text(encoding="utf-8").lower()
    for needle in ("applyvalidator", "patchapplication", "apply workspace",
                   "proposed_changes", "fixed test allowlist", "apply_report",
                   "human review", "not implemented"):
        assert needle in arch, f"arch doc missing: {needle!r}"


def test_readme_links_phase_4_and_states_status():
    # Stable facts: README links the (frozen) Phase 4 checkpoint + report and still
    # marks approved patch application as workspace-only green. (Phase 5 advances the
    # must-know-flags wording; Phase 5's test owns that.)
    text = README.read_text(encoding="utf-8")
    low = text.lower()
    assert "checkpoint-phase-4-approved-patch-application" in text
    assert "reports/phase_4_approved_patch_application/README.md" in text
    assert "approved patch application v0 (workspace-only) is green" in low
    assert "workspace-only" in low


def test_quick_resume_phase_4_and_decision_point():
    low = QUICK_RESUME.read_text(encoding="utf-8").lower()
    assert "checkpoint-phase-4-approved-patch-application" in low
    assert "fake_approved_patch_application" in low
    assert "workspace-only" in low
    assert "no auto promotion" in low
    # promotion is still not started after later phases (merge may ship; promotion not)
    assert "promotion not started" in low
    assert "real provider implementation" in low
    assert "ui dashboard" in low


def test_next_milestone_marks_phase_4_complete():
    low = NEXT_MILESTONE.read_text(encoding="utf-8").lower()
    assert "phase 4" in low and "complete and frozen" in low
    # durable invariants (specific decision-point wording is living and advances)
    assert "must not modify stable directly" in low
    assert "rollback plan" in low
    assert "promotion policy" in low


def test_status_docs_apply_status():
    matrix = CANDIDATE_MATRIX.read_text(encoding="utf-8").lower()
    assert "approvedpatchapplication v0" in matrix
    assert "workspace-only completed" in matrix
    assert "merge" in matrix and "not started" in matrix
    assert "autopromotion" in matrix and "forbidden" in matrix
    assert "stablemodification" in matrix and "forbidden" in matrix
    promo = PROMOTION.read_text(encoding="utf-8").lower()
    assert "approved patch application" in promo
    assert "merge and promotion are not started" in promo or "not authorize" in promo


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
