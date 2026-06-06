import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.apply_validator import (
    APPROVAL_MARKER, ApprovalRecord, parse_approval, validate_for_apply,
)
from src.repair.types import RepairAction, RepairProposal

SECRET = "sk-" + "p" * 40


def _action(id="a1", action_type="update_candidate",
            target="harnesses/candidates/x/", risk="low", approval=False):
    return RepairAction(id=id, action_type=action_type, target=target,
                        risk_level=risk, requires_approval=approval)


def _proposal(actions=None, applied=False):
    return RepairProposal(id="repair_x", failure_type="test_failed",
                          actions=actions or [_action()], applied=applied)


def _approved():
    return ApprovalRecord(approved=True, reviewer="a-human")


def test_approved_proposal_pass():
    assert validate_for_apply(_proposal(), _approved()).valid


def test_missing_approval_rejected():
    r = validate_for_apply(_proposal(), ApprovalRecord(approved=False, reviewer="x"))
    assert not r.valid
    assert any("approval_marker_missing" in e for e in r.errors)


def test_empty_reviewer_rejected():
    r = validate_for_apply(_proposal(), ApprovalRecord(approved=True, reviewer=""))
    assert not r.valid
    assert any("reviewer_empty" in e for e in r.errors)


def test_stable_target_rejected():
    r = validate_for_apply(_proposal([_action(target="skills/inspect_project/")]), _approved())
    assert not r.valid


def test_safety_gate_target_rejected():
    r = validate_for_apply(_proposal([_action(target="src/agents/safety_gate/x.py")]), _approved())
    assert not r.valid


def test_promotion_policy_target_rejected():
    r = validate_for_apply(_proposal([_action(target="specs/harness/promotion_policy.md")]), _approved())
    assert not r.valid


def test_secret_looking_proposal_rejected():
    p = _proposal()
    p.rationale = f"key {SECRET}"
    r = validate_for_apply(p, _approved())
    assert not r.valid
    assert all(SECRET not in e for e in r.errors)


def test_raw_shell_action_rejected():
    for bad in ("raw_shell", "direct_command", "delete_file"):
        r = validate_for_apply(_proposal([_action(action_type=bad)]), _approved())
        assert not r.valid, bad


def test_action_type_not_in_apply_allowlist_rejected():
    # e.g. an unknown action_type the proposal validator might pass but apply won't
    r = validate_for_apply(_proposal([_action(action_type="modify_stable_skill")]), _approved())
    assert not r.valid


def test_applied_proposal_rejected_for_apply():
    r = validate_for_apply(_proposal(applied=True), _approved())
    assert not r.valid


def test_parse_approval_marker_and_reviewer():
    text = f"stuff\n{APPROVAL_MARKER}: true\nReviewer: jane\n"
    a = parse_approval(text)
    assert a.approved and a.reviewer == "jane"
    # missing marker
    assert not parse_approval("Reviewer: jane").approved
    # placeholder reviewer is treated as empty
    a2 = parse_approval(f"{APPROVAL_MARKER}: true\nReviewer: <name>")
    assert a2.approved and a2.reviewer == ""


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
