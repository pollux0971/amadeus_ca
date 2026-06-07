import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

GEN = ROOT / "scripts" / "generate_dashboard_snapshot.py"
GEN_SRC = GEN.read_text(encoding="utf-8")
EXAMPLE = ROOT / "ui_dashboard" / "data" / "dashboard_snapshot.example.json"
INDEX = ROOT / "ui_dashboard" / "static" / "index.html"
APPJS = ROOT / "ui_dashboard" / "static" / "app.js"

_spec = importlib.util.spec_from_file_location("generate_dashboard_snapshot", GEN)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

from src.llm.redaction import redact_text  # noqa: E402

_vd_spec = importlib.util.spec_from_file_location(
    "validate_dashboard", ROOT / "scripts" / "validate_dashboard.py")
vd = importlib.util.module_from_spec(_vd_spec)
_vd_spec.loader.exec_module(vd)

NEW_KEYS = ["openai_provider_status", "planner_live_status", "readonly_execution_status",
            "readonly_allowlist", "latest_gate_scores", "blocked_items"]
NEW_SECTION_IDS = NEW_KEYS  # section ids mirror the keys


def test_snapshot_has_new_gate_status_keys():
    snap = gen.build_snapshot()
    for k in NEW_KEYS:
        assert k in snap, k


def test_readonly_allowlist_is_readonly_only():
    snap = gen.build_snapshot()
    al = snap["readonly_allowlist"]
    assert al == ["inspect_project", "list_project_files"]
    forbidden = {"patch_file_and_run_tests", "start_local_server", "open_localhost_browser",
                 "read_browser_console", "raw_shell", "repair", "apply", "merge",
                 "staging_promote", "promote", "exec", "eval", "bash"}
    assert not (set(al) & forbidden)


def test_latest_gate_scores_lists_readonly_evals():
    rows = gen.build_snapshot()["latest_gate_scores"]
    ids = {r["id"] for r in rows}
    assert "openai_readonly_execution_gate" in ids
    assert "openai_readonly_list_files_execution_gate" in ids
    for r in rows:
        assert r.get("score") == 1.0


def test_blocked_items_includes_stable_promotion():
    items = gen.build_snapshot()["blocked_items"]
    assert any("stable promotion" in i.lower() for i in items)


def test_provider_status_is_fake_default_and_opt_in():
    p = gen.build_snapshot()["openai_provider_status"]
    assert p["fake_provider_default"] is True
    assert p["fail_closed"] is True
    assert "opt-in" in p["real_call"].lower()


def test_planner_status_is_plan_only_no_autorepair():
    p = gen.build_snapshot()["planner_live_status"]
    assert p["mode"] == "plan-only"
    assert p["executes_plan"] is False and p["auto_repair"] is False


def test_snapshot_has_no_secret():
    text = json.dumps(gen.build_snapshot(), ensure_ascii=False)
    assert redact_text(text) == text
    # must not embed the raw key token / authorization marker
    low = text.lower()
    assert "api_key" not in low and "authorization:" not in low


def test_example_snapshot_has_new_keys_and_validates():
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    for k in NEW_KEYS:
        assert k in data, k
    # validate_dashboard accepts the whole skeleton (example included)
    assert vd.check(ROOT) == []


def test_ui_has_new_readonly_sections():
    html = INDEX.read_text(encoding="utf-8")
    ajs = APPJS.read_text(encoding="utf-8")
    for sid in NEW_SECTION_IDS:
        assert f'id="{sid}"' in html, sid
        assert sid in ajs, sid


def test_ui_stays_read_only_no_action():
    low = INDEX.read_text(encoding="utf-8").lower()
    for pat in ("<form", "method=\"post\"", "onclick=", "<button"):
        assert pat not in low, pat


def test_generator_reads_no_secret_source_no_subprocess():
    # The generator must not read .env/password/runs raw, and must run no shell.
    assert "shell=True" not in GEN_SRC and "os.system" not in GEN_SRC
    assert "subprocess" not in GEN_SRC
    # still guards the safe read roots and refuses on secret
    assert "refusing to write" in GEN_SRC.lower() or "blocked" in GEN_SRC.lower()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
