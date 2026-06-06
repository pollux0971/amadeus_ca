import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.proposal_validator import validate_proposal
from src.repair.types import RepairAction, RepairProposal

SECRET = "sk-ant-" + "k" * 40


def _action(id="a1", action_type="update_candidate",
            target="harnesses/candidates/x/", risk="low", approval=False):
    return RepairAction(id=id, action_type=action_type, target=target,
                        risk_level=risk, requires_approval=approval)


def _proposal(actions=None, applied=False):
    return RepairProposal(id="repair_x", failure_type="test_failed",
                          actions=actions or [_action()], applied=applied)


def test_valid_proposal_pass():
    p = _proposal([_action("a1", "update_candidate", "harnesses/candidates/c/"),
                   _action("a2", "add_test", "tests/unit/test_x.py")])
    assert validate_proposal(p).valid


def test_modify_stable_skill_rejected():
    # via forbidden action_type
    p = _proposal([_action(action_type="modify_stable_skill", target="harnesses/candidates/c/")])
    assert not validate_proposal(p).valid
    # via forbidden target path
    p2 = _proposal([_action(action_type="update_candidate", target="skills/inspect_project/")])
    r = validate_proposal(p2)
    assert not r.valid
    assert any("outside allowed roots" in e or "protected" in e for e in r.errors)


def test_modify_safety_gate_rejected():
    p = _proposal([_action(action_type="modify_safety_gate", target="src/agents/safety_gate/")])
    assert not validate_proposal(p).valid
    p2 = _proposal([_action(action_type="update_docs", target="src/agents/safety_gate/x.py")])
    assert not validate_proposal(p2).valid


def test_modify_promotion_policy_rejected():
    p = _proposal([_action(action_type="modify_promotion_policy",
                           target="specs/harness/promotion_policy.md")])
    assert not validate_proposal(p).valid
    p2 = _proposal([_action(action_type="update_docs",
                            target="specs/harness/promotion_policy.md")])
    assert not validate_proposal(p2).valid


def test_raw_shell_rejected():
    for bad in ("raw_shell", "direct_command", "delete_file", "exec", "bash"):
        p = _proposal([_action(action_type=bad, target="harnesses/candidates/c/")])
        assert not validate_proposal(p).valid, bad


def test_secret_looking_proposal_rejected():
    p = _proposal([_action(target="harnesses/candidates/c/")])
    p.rationale = f"use key {SECRET}"
    r = validate_proposal(p)
    assert not r.valid
    assert any("secret-looking" in e for e in r.errors)
    assert all(SECRET not in e for e in r.errors)


def test_high_risk_without_approval_rejected():
    p = _proposal([_action(risk="high", approval=False)])
    assert not validate_proposal(p).valid
    p2 = _proposal([_action(risk="high", approval=True)])
    assert validate_proposal(p2).valid


def test_applied_proposal_rejected():
    p = _proposal(applied=True)
    r = validate_proposal(p)
    assert not r.valid
    assert any("applied" in e for e in r.errors)


def test_duplicate_action_id_rejected():
    p = _proposal([_action("dup"), _action("dup", "add_test", "tests/unit/t.py")])
    assert not validate_proposal(p).valid


def test_target_must_be_in_allowed_roots():
    p = _proposal([_action(target="random/place/file.py")])
    assert not validate_proposal(p).valid
    for ok in ("harnesses/candidates/c/", "tests/x.py", "evals/y.yaml",
               "docs/z.md", "reports/r.md"):
        assert validate_proposal(_proposal([_action(target=ok)])).valid, ok


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
