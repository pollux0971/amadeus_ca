import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

_SCRIPT = ROOT / "scripts" / "validate_candidate_docs.py"
_spec = importlib.util.spec_from_file_location("validate_candidate_docs_under_test", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def test_required_docs_exist():
    for rel in mod.REQUIRED_DOCS:
        assert (ROOT / rel).exists(), f"missing {rel}"


def test_candidate_docs_pass_all_statements():
    errors = mod.check(ROOT)
    assert errors == [], errors


def test_key_policy_statements_present():
    combined = "\n".join((ROOT / d).read_text(encoding="utf-8") for d in mod.REQUIRED_DOCS).lower()
    assert "read_browser_console" in combined and "blocked" in combined
    assert "open_localhost_browser" in combined and "playwright" in combined
    assert "http_fallback is not a real browser" in combined


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
