import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RP = ROOT / "docs" / "real_provider"
REPORT = ROOT / "reports" / "story_real_provider_v0" / "README.md"
STORY = ROOT / "docs" / "epics" / "stories" / "story_real_provider_v0.md"


def test_planning_docs_exist():
    for f in ("README.md", "threat_model.md", "env_var_loading_policy.md",
              "redaction_test_plan.md"):
        assert (RP / f).exists(), f
    assert REPORT.exists()


def test_planning_only_boundaries_written():
    combined = ""
    for f in ("README.md", "threat_model.md", "env_var_loading_policy.md",
              "redaction_test_plan.md"):
        combined += (RP / f).read_text(encoding="utf-8").lower() + "\n"
    assert "planning" in combined
    assert "no real api call" in combined or "no real api" in combined
    assert "no provider client" in combined or "no real provider implemented" in combined
    assert "fake provider" in combined and ("default" in combined)
    assert "fail closed" in combined or "fail-closed" in combined
    assert "password_and_api.txt" in combined  # explicitly never read
    assert "env var" in combined and "name" in combined  # env-var-name only
    assert "redact" in combined


def test_threat_model_has_threats_and_mitigations():
    tm = (RP / "threat_model.md").read_text(encoding="utf-8").lower()
    assert "threat" in tm and "mitigation" in tm
    assert "key" in tm and "redact" in tm
    assert "operator opt-in" in tm or "opt-in" in tm


def test_env_var_policy_is_named_env_only():
    ev = (RP / "env_var_loading_policy.md").read_text(encoding="utf-8").lower()
    assert "named environment variable" in ev or "named env var" in ev or "env var name" in ev
    assert "password_and_api.txt" in ev and "never" in ev
    assert "no key in" in ev or "never a key value" in ev or "env var **name**" in ev or "env var name" in ev
    assert "fail closed" in ev or "fail-closed" in ev


def test_redaction_test_plan_has_cases():
    rt = (RP / "redaction_test_plan.md").read_text(encoding="utf-8").lower()
    assert "redact" in rt
    assert "synthetic" in rt  # no real key in tests
    assert "no real api call" in rt or "makes no real api call" in rt
    assert "fail-closed" in rt or "fail closed" in rt


def test_fake_provider_still_default_and_no_secret_in_docs():
    # fake provider still works + loader still fails closed (no runtime change made)
    from src.llm.config_loader import build_provider
    from src.llm.fake_provider import FakeLLMProvider
    prov = build_provider(config={"llm": {"provider": "fake", "redact_secrets": True}})
    assert isinstance(prov, FakeLLMProvider)
    assert prov.real_api_enabled is False
    # no secret-looking content in the planning docs / report
    from src.llm.redaction import redact_text
    assert "done" in STORY.read_text(encoding="utf-8").lower()
    for f in list(RP.iterdir()) + [REPORT]:
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert redact_text(text) == text, f"secret-like content in {f}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
