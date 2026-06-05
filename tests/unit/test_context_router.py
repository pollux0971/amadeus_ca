from src.harness.context_router import ContextState, build_context_packet, choose_context_strategy


def test_failure_uses_failure_focused_context():
    state = ContextState(total_steps=5, context_tokens_estimated=1000, latest_step_failed=True)
    assert choose_context_strategy(state) == "failure_focused"


def test_repeated_failures_discard_noise():
    state = ContextState(total_steps=8, context_tokens_estimated=4000, repeated_failure_count=2)
    assert choose_context_strategy(state) == "discard_noise_reinject_plan"


def test_large_context_uses_summary_with_pinned_evidence():
    state = ContextState(total_steps=10, context_tokens_estimated=9000)
    assert choose_context_strategy(state) == "summary_with_pinned_evidence"


def test_build_context_packet_contains_safety_note():
    packet = build_context_packet("fix app", "read console", "keep_last_n")
    assert packet["goal"]["original_user_goal"] == "fix app"
    assert any("untrusted browser" in note for note in packet["notes"])
