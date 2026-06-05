import http.server
import importlib.util
import json
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

CAND = Path(__file__).resolve().parents[1]
SCRIPT = CAND / "scripts" / "open_localhost_browser.py"
_spec = importlib.util.spec_from_file_location("candidate_browser_under_test", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

_HTML = (
    b"<!doctype html><html><head><title>Test Page</title></head>"
    b"<body><h1>hi</h1><a href='/x'>Link</a><button>Go</button>"
    b"<form action='/s' method='post'><input type='submit' value='Send'></form>"
    b"some visible text</body></html>"
)


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(_HTML)

    def log_message(self, *args):  # silence
        pass


class _LiveServer:
    def __enter__(self):
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()
        host, port = self.srv.server_address
        self.url = f"http://127.0.0.1:{port}/"
        return self

    def __exit__(self, *exc):
        self.srv.shutdown()
        self.srv.server_close()


def test_explicit_localhost_url_accepted():
    with _LiveServer() as s:
        d = tempfile.mkdtemp()
        r = mod.open_localhost_browser(server_url=s.url, artifacts_dir=d + "/a")
        assert r["status"] == "loaded", r
        assert r["status_code"] == 200
        assert r["title"] == "Test Page"
        assert r["browser_closed"] is True


def test_non_localhost_url_rejected():
    r = mod.open_localhost_browser(server_url="http://example.com/")
    assert r["status"] == "failed"
    assert r["failure_reason"] == "url_not_allowed"
    # must not have loaded anything
    assert r["status_code"] is None


def test_reads_server_url_from_session_file():
    with _LiveServer() as s:
        d = Path(tempfile.mkdtemp())
        session_file = d / "server_session.json"
        session_file.write_text(json.dumps({"server_url": s.url}), encoding="utf-8")
        r = mod.open_localhost_browser(server_session_path=str(session_file), artifacts_dir=str(d / "a"))
        assert r["status"] == "loaded", r
        assert r["url"] == s.url


def test_missing_server_url_fails():
    r = mod.open_localhost_browser()
    assert r["status"] == "failed"
    assert r["failure_reason"] == "no_server_url"


def test_browser_runtime_missing_graceful():
    # Simulate no Playwright AND no fallback -> graceful browser_runtime_missing.
    original = mod._playwright_available
    mod._playwright_available = lambda: False
    try:
        with _LiveServer() as s:
            r = mod.open_localhost_browser(server_url=s.url, allow_http_fallback=False)
        assert r["status"] == "failed"
        assert r["failure_reason"] == "browser_runtime_missing"
    finally:
        mod._playwright_available = original


def test_page_snapshot_created_on_success():
    with _LiveServer() as s:
        d = Path(tempfile.mkdtemp())
        r = mod.open_localhost_browser(server_url=s.url, artifacts_dir=str(d / "a"))
        assert r["page_snapshot_ref"]
        snap_path = d / "a" / "page_snapshot.json"
        assert snap_path.exists()
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
        for key in ("url", "title", "visible_text_preview", "links", "buttons", "forms", "counts"):
            assert key in snap, f"snapshot missing {key}"
        assert snap["counts"]["links"] == 1
        assert snap["counts"]["forms"] == 1
        assert snap["counts"]["buttons"] >= 1


def test_browser_resources_closed_and_result_written():
    with _LiveServer() as s:
        d = Path(tempfile.mkdtemp())
        r = mod.open_localhost_browser(server_url=s.url, artifacts_dir=str(d / "a"))
        assert r["browser_closed"] is True
        assert (d / "a" / "result.json").exists()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
