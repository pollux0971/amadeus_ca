import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHECKPOINT = ROOT / "docs" / "checkpoints" / "checkpoint-0-to-1-harness-gates.md"
README = ROOT / "README.md"
QUICK_RESUME = ROOT / "docs" / "quick_resume.md"
_LINK = "docs/checkpoints/checkpoint-0-to-1-harness-gates.md"


def test_checkpoint_doc_exists():
    assert CHECKPOINT.exists()


def test_checkpoint_freezes_gate_status():
    low = CHECKPOINT.read_text(encoding="utf-8").lower()
    for needle in (
        "patch_file_and_run_tests_v2",
        "start_local_server_v1.2",
        "open_localhost_browser_v1",
        "read_browser_console",
        "blocked",
        "http_fallback is not a real browser",
        "walking skeleton",
    ):
        assert needle in low, f"checkpoint missing '{needle}'"
    # the gates are recorded as existing-but-not-executed / blocked
    assert "have not been executed" in low or "not been executed" in low
    assert "draft" in low


def test_readme_and_quick_resume_link_to_checkpoint():
    assert _LINK in README.read_text(encoding="utf-8")
    assert "checkpoints/checkpoint-0-to-1-harness-gates.md" in QUICK_RESUME.read_text(encoding="utf-8")


def test_validator_includes_checkpoint():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "validate_candidate_docs_ck", ROOT / "scripts" / "validate_candidate_docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert _LINK in mod.REQUIRED_FILES
    assert mod.check(ROOT) == []  # everything wired and present


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
