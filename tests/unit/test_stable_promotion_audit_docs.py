import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "stable_promotion_readiness_audit_v0"

DOC_FILES = [
    "README.md", "01_current_state.md", "02_gate_results.md", "03_risk_register.md",
    "04_go_no_go_recommendation.md", "05_required_human_review.md",
]


def test_audit_files_exist():
    for f in DOC_FILES:
        assert (AUD / f).exists(), f


def test_required_content_present():
    combined = ""
    for f in DOC_FILES:
        combined += (AUD / f).read_text(encoding="utf-8").lower() + "\n"
    for phrase in ("latest checkpoint", "phase 1b", "phase 6", "dashboard",
                   "demo package", "fake provider", "no real api",
                   "rollback verification", "regression", "shell-execution review",
                   "operator approval", "remaining blocker", "stable skills",
                   "safety_gate", "promotion_policy"):
        assert phrase in combined, f"audit missing phrase {phrase!r}"


def test_recommendation_is_no_go_or_blocked():
    rec = (AUD / "04_go_no_go_recommendation.md").read_text(encoding="utf-8").lower()
    assert "no-go" in rec or "blocked" in rec
    assert "recommendation" in rec


def test_does_not_claim_promotion_completed():
    combined = ""
    for f in DOC_FILES:
        combined += (AUD / f).read_text(encoding="utf-8").lower() + "\n"
    for bad in ("stable promotion completed", "stable promotion is complete",
                "stable promotion done", "promoted to stable"):
        assert bad not in combined, f"audit falsely claims {bad!r}"


def test_human_gates_flagged_unmet():
    gr = (AUD / "02_gate_results.md").read_text(encoding="utf-8").lower()
    assert "not satisfied" in gr
    for gate in ("shell-execution review", "promotion-policy review",
                 "operator approval", "rollback"):
        assert gate in gr, f"gate results missing {gate!r}"
    rr = (AUD / "03_risk_register.md").read_text(encoding="utf-8").lower()
    assert "blocking" in rr


def test_required_human_review_is_a_checklist():
    hr = (AUD / "05_required_human_review.md").read_text(encoding="utf-8").lower()
    assert "[ ]" in hr  # unchecked human action items
    assert "shell-execution review" in hr and "operator approval" in hr
    assert "cannot be done by automation" in hr or "human actions" in hr or "not this audit" in hr


def test_entry_points_link_audit():
    for doc in ("README.md", "docs/quick_resume.md", "docs/next_milestone_plan.md",
                "docs/promotion_readiness_review.md"):
        assert "stable_promotion_readiness_audit_v0" in (ROOT / doc).read_text(encoding="utf-8"), doc


def test_no_secret_in_audit():
    from src.llm.redaction import redact_text
    for f in AUD.iterdir():
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert redact_text(text) == text, f"secret-like content in {f}"


def test_validator_passes():
    spec = importlib.util.spec_from_file_location(
        "validate_stable_promotion_audit", ROOT / "scripts" / "validate_stable_promotion_audit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check(ROOT) == [], mod.check(ROOT)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
