import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EPICS = ROOT / "docs" / "epics"
README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"
NEXT_MILESTONE = ROOT / "docs" / "next_milestone_plan.md"

EPIC_FILES = [
    "epic_stable_promotion.md",
    "epic_ui_dashboard.md",
    "epic_real_provider.md",
    "epic_multimodal_data_channels.md",
]
STORY_FILES = [
    "stories/story_stable_promotion_v0.md",
    "stories/story_ui_dashboard_v0.md",
    "stories/story_real_provider_v0.md",
    "stories/story_multimodal_channel_v0.md",
]
STORY_SECTIONS = ["acceptance criteria", "forbidden zone", "validation commands", "stop condition"]


def test_backlog_structure_exists():
    for f in ("README.md", "epic_overview.md", "story_template.md", "decision_matrix.md"):
        assert (EPICS / f).exists(), f
    for f in EPIC_FILES:
        assert (EPICS / f).exists(), f
    assert len(EPIC_FILES) >= 4
    for f in STORY_FILES:
        assert (EPICS / f).exists(), f
    assert len(STORY_FILES) >= 4


def test_each_story_has_required_sections():
    for f in STORY_FILES:
        low = (EPICS / f).read_text(encoding="utf-8").lower()
        for section in STORY_SECTIONS:
            assert section in low, f"{f} missing section {section!r}"


def test_each_story_has_full_template_fields():
    fields = ["goal", "scope", "out of scope", "preconditions",
              "implementation boundaries", "acceptance criteria", "forbidden zone",
              "validation commands", "artifacts", "stop condition", "definition of done"]
    for f in STORY_FILES:
        low = (EPICS / f).read_text(encoding="utf-8").lower()
        for field in fields:
            assert field in low, f"{f} missing field {field!r}"


def test_story_template_has_fields():
    low = (EPICS / "story_template.md").read_text(encoding="utf-8").lower()
    for field in ("goal", "scope", "acceptance criteria", "forbidden zone",
                  "validation commands", "stop condition", "definition of done"):
        assert field in low, f"template missing {field!r}"


def test_decision_matrix_compares_four_options():
    low = (EPICS / "decision_matrix.md").read_text(encoding="utf-8").lower()
    for opt in ("stable promotion", "ui dashboard", "real provider", "multimodal"):
        assert opt in low, f"decision_matrix missing {opt!r}"
    for col in ("value", "risk", "dependencies", "required gates",
                "reason to choose now", "reason to defer"):
        assert col in low, f"decision_matrix missing column {col!r}"


def test_backlog_states_hard_boundaries():
    combined = ""
    for f in ["README.md", "epic_overview.md", *EPIC_FILES, *STORY_FILES,
              "story_template.md", "decision_matrix.md"]:
        combined += (EPICS / f).read_text(encoding="utf-8").lower() + "\n"
    for phrase in ("one bounded story", "no real api", "no stable modification",
                   "no raw shell", "no secret"):
        assert phrase in combined, f"backlog missing constraint {phrase!r}"


def test_epic_specific_boundaries():
    stable = (EPICS / "epic_stable_promotion.md").read_text(encoding="utf-8").lower()
    assert "promotion policy" in stable and "rollback" in stable
    assert "human shell-execution review" in stable
    ui = (EPICS / "epic_ui_dashboard.md").read_text(encoding="utf-8").lower()
    assert "redacted" in ui and "raw shell" in ui and "promote" in ui
    provider = (EPICS / "epic_real_provider.md").read_text(encoding="utf-8").lower()
    assert "password_and_api.txt" in provider
    assert "env var" in provider and "fake provider" in provider and "fail closed" in provider
    mm = (EPICS / "epic_multimodal_data_channels.md").read_text(encoding="utf-8").lower()
    assert "isolation" in mm and "untrusted" in mm and "eval" in mm


def test_entry_points_link_the_backlog():
    assert "docs/epics" in README.read_text(encoding="utf-8")
    assert "epics/" in QUICK_RESUME.read_text(encoding="utf-8")
    nm = NEXT_MILESTONE.read_text(encoding="utf-8").lower()
    assert "one bounded story" in nm
    assert "decision_matrix" in nm


def test_validate_epics_passes():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "validate_epics", ROOT / "scripts" / "validate_epics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    errors = mod.check(ROOT)
    assert errors == [], errors


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
