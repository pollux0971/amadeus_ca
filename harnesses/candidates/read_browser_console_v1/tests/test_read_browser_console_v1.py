import http.server
import importlib.util
import json
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

CAND = Path(__file__).resolve().parents[1]
SCRIPT = CAND / "scripts" / "read_browser_console.py"
_spec = importlib.util.spec_from_file_location("candidate_console_under_test", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

_HAS_PW = importlib.util.find_spec("playwright") is not None

_CONSOLE_HTML = (
    b"<!doctype html><html><head><title>T</title></head><body>"
    b"<script>console.log('hello');console.info('i');console.warn('w');console.error('e');</script>"
    b"</body></html>"
)
_THROW_HTML = (
    b"<!doctype html><html><head><title>T</title></head><body>"
    b"<script>throw new Error('kaboom');</script></body></html>"
)


class _LiveServer:
    def __init__(self, body):
        self._body = body
        self.hits = 0

    def __enter__(self):
        body = self._body
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                outer.hits += 1
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/"
        return self

    def __exit__(self, *exc):
        self.srv.shutdown()
        self.srv.server_close()


# ---- always-run (no Playwright needed) ----

def test_http_fallback_rejected():
    r = mod.read_browser_console(server_url="http://127.0.0.1:1/", browser_mode="http_fallback")
    assert r["status"] == "failed"
    assert r["failure_reason"] == "http_fallback_not_allowed"
    assert r["is_real_browser"] is False


def test_non_localhost_rejected():
    r = mod.read_browser_console(server_url="http://example.com/", browser_mode="playwright")
    assert r["failure_reason"] == "url_not_allowed"


def test_missing_url_fails():
    r = mod.read_browser_console(browser_mode="playwright")
    assert r["failure_reason"] == "missing_server_url"


def test_missing_runtime_graceful_fail():
    original = mod._playwright_available
    mod._playwright_available = lambda: False
    try:
        r = mod.read_browser_console(server_url="http://127.0.0.1:1/", browser_mode="playwright")
        assert r["status"] == "failed"
        assert r["failure_reason"] == "browser_runtime_missing"
        assert r["console_supported"] is False
        # back-compat keys always present
        assert r["console_errors"] == [] and r["fatal_error_count"] == 0
    finally:
        mod._playwright_available = original


def test_result_schema_always_has_keys():
    r = mod.read_browser_console(browser_mode="playwright")  # fails (missing url)
    for k in ("status", "engine", "is_real_browser", "console_supported",
              "console_counts", "console_errors", "fatal_error_count",
              "browser_closed", "failure_reason"):
        assert k in r, k
    for c in ("fatal", "error", "warning", "info", "debug", "total"):
        assert c in r["console_counts"]


def test_classify_console_type():
    assert mod.classify_console_type("error") == "error"
    assert mod.classify_console_type("warning") == "warning"
    assert mod.classify_console_type("info") == "info"
    assert mod.classify_console_type("log") == "debug"


# ---- Playwright-only (skip gracefully without a real browser) ----

def test_console_classification_real_browser():
    if not _HAS_PW:
        return
    with _LiveServer(_CONSOLE_HTML) as s:
        d = tempfile.mkdtemp()
        r = mod.read_browser_console(server_url=s.url, browser_mode="playwright",
                                     wait_after_load_ms=400, artifacts_dir=d + "/a")
        assert r["status"] == "collected", r
        assert r["engine"] == "playwright" and r["is_real_browser"] is True
        assert r["console_supported"] is True
        c = r["console_counts"]
        assert c["error"] == 1 and c["warning"] == 1 and c["info"] == 1 and c["debug"] == 1
        assert c["fatal"] == 0
        assert r["has_console_error"] is True and r["has_fatal_console_error"] is False
        cl = json.loads(Path(d + "/a/console_log.json").read_text(encoding="utf-8"))
        assert {e["category"] for e in cl["entries"]} == {"error", "warning", "info", "debug"}


def test_pageerror_captured_as_fatal():
    if not _HAS_PW:
        return
    with _LiveServer(_THROW_HTML) as s:
        d = tempfile.mkdtemp()
        r = mod.read_browser_console(server_url=s.url, browser_mode="playwright",
                                     wait_after_load_ms=400, artifacts_dir=d + "/a")
        assert r["status"] == "collected", r
        assert r["console_counts"]["fatal"] >= 1
        assert r["has_fatal_console_error"] is True
        cl = json.loads(Path(d + "/a/console_log.json").read_text(encoding="utf-8"))
        assert len(cl["page_errors"]) >= 1
        assert "kaboom" in cl["page_errors"][0]["message"]


def test_browser_resources_closed_and_does_not_kill_server():
    if not _HAS_PW:
        return
    with _LiveServer(_CONSOLE_HTML) as s:
        r = mod.read_browser_console(server_url=s.url, browser_mode="playwright",
                                     wait_after_load_ms=300, artifacts_dir=tempfile.mkdtemp())
        assert r["browser_closed"] is True
        # server must still be serving (skill must NOT kill it)
        with urllib.request.urlopen(s.url, timeout=5) as resp:
            assert resp.getcode() == 200
        assert s.hits >= 2  # the skill's load + this probe


def test_smoke_eval_scores_1_when_playwright_present():
    if not _HAS_PW:
        return
    from src.skills_runtime.simple_yaml import load_yaml
    from src.orchestrator.orchestrator import Orchestrator
    task = load_yaml(ROOT / "evals" / "browser" / "read_browser_console_smoke.yaml")
    tmp = tempfile.mkdtemp(prefix="console_e2e_")
    orch = Orchestrator(task["id"], task["user_goal"], runs_dir=tmp)
    run_dir = orch.run_eval_task(task, eval_path=ROOT / "evals" / "browser" / "read_browser_console_smoke.yaml")
    score = json.loads((run_dir / "score.json").read_text(encoding="utf-8"))
    assert score["task_success"] is True and score["score"] == 1.0, score
    crit = {r["criterion"]: r["passed"] for r in score["criteria_results"]}
    assert crit["console_collected"] and crit["engine_playwright"] and crit["console_supported_true"]
    # server torn down by the orchestrator finally
    for sess in orch._server_sessions:
        try:
            import os
            os.kill(sess["pid"], 0)
            alive = True
        except (ProcessLookupError, OSError):
            alive = False
        assert not alive, "server lingered"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}" + ("" if _HAS_PW else " (note: pw-only tests skipped if no playwright)"))
