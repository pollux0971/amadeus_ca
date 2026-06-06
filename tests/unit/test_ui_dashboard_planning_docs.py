import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

UID = ROOT / "docs" / "ui_dashboard"
REPORT = ROOT / "reports" / "story_ui_dashboard_v0" / "README.md"
STORY = ROOT / "docs" / "epics" / "stories" / "story_ui_dashboard_v0.md"


def test_planning_docs_exist():
    for f in ("README.md", "information_architecture.md",
              "redacted_artifact_model.md", "future_eval_list.md"):
        assert (UID / f).exists(), f
    assert REPORT.exists()


def test_planning_only_no_action_no_secret():
    combined = ""
    for f in ("README.md", "information_architecture.md",
              "redacted_artifact_model.md", "future_eval_list.md"):
        combined += (UID / f).read_text(encoding="utf-8").lower() + "\n"
    # boundaries from the epic/story must be written down
    assert "planning only" in combined
    assert "read-only" in combined
    assert "no action execution" in combined or "no action" in combined
    assert "no raw shell" in combined
    assert "no secret" in combined or "no secret display" in combined
    assert "no promotion from ui" in combined or "no promote" in combined
    assert "redact" in combined  # redacted artifact model


def test_information_architecture_is_read_only():
    ia = (UID / "information_architecture.md").read_text(encoding="utf-8").lower()
    assert "read-only" in ia
    # explicitly excludes an executing button
    assert "button that executes" in ia or "no action" in ia
    # references the real artifact roots, not a live control surface
    for src in ("runs/", "reports/", "docs/checkpoints", "evals/"):
        assert src in ia, src


def test_redacted_model_never_shows_secret():
    rm = (UID / "redacted_artifact_model.md").read_text(encoding="utf-8").lower()
    assert "redact" in rm
    assert "password_and_api.txt" in rm  # explicitly never read
    assert "never" in rm


def test_future_eval_list_has_entries():
    fe = (UID / "future_eval_list.md").read_text(encoding="utf-8").lower()
    assert "eval" in fe
    assert "no eval implemented" in fe or "no eval" in fe
    # at least references the redaction + no-action future evals
    assert "redaction" in fe and ("no_action" in fe or "no action" in fe or "no promotion" in fe)


def test_story_marked_done_and_no_secret_in_docs():
    from src.llm.redaction import redact_text
    assert "done" in STORY.read_text(encoding="utf-8").lower()
    for f in list(UID.iterdir()) + [REPORT]:
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert redact_text(text) == text, f"secret-like content in {f}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
