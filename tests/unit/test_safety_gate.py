from src.agents.safety_gate.command_policy import check_command

def test_blocks_rm_rf():
    allowed, reason = check_command("rm -rf /tmp/test")
    assert not allowed
    assert reason

def test_allows_pytest():
    allowed, reason = check_command("pytest -q")
    assert allowed
    assert reason is None
