import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SCRIPT = ROOT / "scripts" / "check_secret_hygiene.py"
_spec = importlib.util.spec_from_file_location("check_secret_hygiene_under_test", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

GITIGNORE = ROOT / ".gitignore"
ENV_EXAMPLE = ROOT / ".env.example"


def test_script_exists():
    assert SCRIPT.exists()


def test_gitignore_has_required_rules():
    lines = {ln.strip() for ln in GITIGNORE.read_text(encoding="utf-8").splitlines()}
    for rule in (".env", ".env.*", "*.env", "password_and_api.txt",
                 "secrets/", ".secrets/", "*.key", "*.pem"):
        assert rule in lines, f".gitignore missing {rule}"
    assert ("runs/" in lines) or ("runs/*" in lines)
    # the standalone check agrees there is nothing missing
    assert mod.missing_gitignore_rules(ROOT) == []


def test_env_example_has_no_real_key():
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    # placeholders present, values empty / fake
    assert "OPENAI_API_KEY=" in text and "ANTHROPIC_API_KEY=" in text
    assert "LLM_PROVIDER=fake" in text
    # no key value after the '=' on the key lines
    for line in text.splitlines():
        if line.startswith(("OPENAI_API_KEY", "ANTHROPIC_API_KEY")):
            assert line.split("=", 1)[1].strip() == "", f"non-empty key value: {line!r}"
    # and no high-confidence key pattern anywhere in the template
    for rx in mod.KEY_PATTERNS.values():
        assert rx.search(text) is None


def test_repo_is_clean_no_tracked_secret_or_key():
    res = mod.check(ROOT)
    assert res["tracked_secret_files"] == []
    assert res["key_findings"] == []


def test_scanner_reports_filename_and_risk_but_not_the_secret_value():
    # Build a fake key at runtime (so this test file never contains a real one).
    fake_key = "sk-" + "a" * 40
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "leak.txt").write_text(f"OPENAI_API_KEY={fake_key}\n", encoding="utf-8")
        # Point the scanner at our temp file (bypassing git in a non-repo dir).
        original = mod._git_tracked
        mod._git_tracked = lambda r: ["leak.txt"]
        try:
            findings = mod.scan_tracked_for_keys(root)
        finally:
            mod._git_tracked = original
    assert findings, "scanner should have flagged the fake key file"
    # The finding reports (filename, risk_name) — and NEVER the secret value.
    for item in findings:
        flat = " ".join(str(x) for x in item)
        assert fake_key not in flat, "scanner leaked the secret value!"
        assert item[0] == "leak.txt"
        assert item[1] in mod.KEY_PATTERNS


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
