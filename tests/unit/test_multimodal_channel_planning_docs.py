import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MM = ROOT / "docs" / "multimodal_data_channels"
REPORT = ROOT / "reports" / "story_multimodal_channel_v0" / "README.md"
STORY = ROOT / "docs" / "epics" / "stories" / "story_multimodal_channel_v0.md"

DOC_FILES = ["README.md", "source_isolation_model.md", "untrusted_content_policy.md",
             "artifact_storage_policy.md", "eval_plan.md"]


def test_planning_docs_exist():
    for f in DOC_FILES:
        assert (MM / f).exists(), f
    assert REPORT.exists()


def test_planning_only_boundaries_written():
    combined = ""
    for f in DOC_FILES:
        combined += (MM / f).read_text(encoding="utf-8").lower() + "\n"
    for phrase in (
        "planning only",
        "no runtime implementation",
        "no new data channel implemented",
        "source isolation",
        "data, not instruction",
        "browser content cannot trigger tool / repair / promotion",
        "must be redacted",
        "each channel requires its own eval",
        "no secret in artifacts",
        "no stable modification",
        "no raw shell",
        "no real api",
    ):
        assert phrase in combined, f"missing phrase: {phrase!r}"


def test_source_isolation_data_vs_control():
    s = (MM / "source_isolation_model.md").read_text(encoding="utf-8").lower()
    assert "data plane" in s and "control plane" in s
    assert "source isolation" in s


def test_untrusted_content_is_not_instruction():
    u = (MM / "untrusted_content_policy.md").read_text(encoding="utf-8").lower()
    assert "data, not instruction" in u
    assert "trigger a tool / repair / promotion" in u or "trigger tool / repair / promotion" in u
    assert "prompt-injection" in u or "injection" in u


def test_artifact_storage_redacted_gitignored():
    a = (MM / "artifact_storage_policy.md").read_text(encoding="utf-8").lower()
    assert "redact" in a and "gitignored" in a
    assert "no secret" in a


def test_eval_plan_per_channel():
    e = (MM / "eval_plan.md").read_text(encoding="utf-8").lower()
    assert "each channel requires its own eval" in e
    assert "adversarial" in e
    assert "no eval is implemented" in e or "no eval implemented" in e


def test_story_done_and_no_secret_in_docs():
    from src.llm.redaction import redact_text
    assert "done" in STORY.read_text(encoding="utf-8").lower()
    for f in list(MM.iterdir()) + [REPORT]:
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert redact_text(text) == text, f"secret-like content in {f}"


def test_validator_passes():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "validate_multimodal_planning", ROOT / "scripts" / "validate_multimodal_planning.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check(ROOT) == [], mod.check(ROOT)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
