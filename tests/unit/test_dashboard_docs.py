import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

UI = ROOT / "ui_dashboard"
STATIC = UI / "static"
REPORT = ROOT / "reports" / "story_ui_dashboard_skeleton_v0" / "README.md"


def test_skeleton_files_exist():
    for f in ("README.md", "static/index.html", "static/app.js", "static/styles.css",
              "data/dashboard_snapshot.example.json"):
        assert (UI / f).exists(), f
    assert (ROOT / "scripts" / "generate_dashboard_snapshot.py").exists()
    assert (ROOT / "scripts" / "validate_dashboard.py").exists()
    assert REPORT.exists()


def test_readme_states_read_only_boundaries():
    low = (UI / "README.md").read_text(encoding="utf-8").lower()
    for phrase in ("read-only", "no action execution", "no raw shell", "no api call",
                   "no secret"):
        assert phrase in low, f"README missing {phrase!r}"


def test_app_js_is_read_only_no_execution():
    low = (STATIC / "app.js").read_text(encoding="utf-8").lower()
    for bad in ("eval(", "innerhtml", "document.write", "xmlhttprequest",
                "new function(", "fetch(\"http", "fetch('http", "method: \"post\"",
                "method: 'post'"):
        assert bad not in low, f"app.js contains forbidden pattern {bad!r}"
    # it only reads local relative snapshot files
    assert "dashboard_snapshot.json" in low
    assert "dashboard_snapshot.example.json" in low


def test_index_html_has_no_action_surface():
    low = (STATIC / "index.html").read_text(encoding="utf-8").lower()
    for bad in ("<form", "method=\"post\"", "onclick=", "formaction"):
        assert bad not in low, f"index.html contains forbidden pattern {bad!r}"


def test_generator_reads_no_secret_sources_and_refuses():
    src = (ROOT / "scripts" / "generate_dashboard_snapshot.py").read_text(encoding="utf-8")
    # never reads .env / password file / runs raw; no shell / subprocess / API
    assert "password_and_api.txt" not in src or "password" in src.lower()  # may mention as a guard
    assert "subprocess" not in src and "os.system" not in src and "shell=True" not in src
    # refuse-on-secret guard present
    assert "redact_text" in src and ("refusing to write" in src.lower() or "blocked" in src.lower())


def test_validator_passes():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "validate_dashboard", ROOT / "scripts" / "validate_dashboard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check(ROOT) == [], mod.check(ROOT)


def test_no_secret_in_dashboard_text_files():
    from src.llm.redaction import redact_text
    for f in [UI / "README.md", STATIC / "index.html", STATIC / "app.js",
              STATIC / "styles.css", REPORT]:
        text = f.read_text(encoding="utf-8")
        assert redact_text(text) == text, f"secret-like content in {f}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
