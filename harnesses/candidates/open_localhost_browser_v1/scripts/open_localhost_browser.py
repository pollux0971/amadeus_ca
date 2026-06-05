"""Candidate open_localhost_browser v1 — load a live localhost server_url.

Consumes a server_url produced by a kept-alive start_local_server (it does NOT
start or tear down any server). It opens the page, builds a small page snapshot
for smoke verification, writes artifacts, and always closes its browser
resources.

Engine selection (most capable first):
  1. Playwright (real headless browser) — used automatically when the
     `playwright` package and a browser binary are available.
  2. HTTP fallback (urllib + html.parser) — loads and smoke-verifies the page
     without a real browser (no JS execution, no rendering, no screenshot).
If neither is usable (Playwright missing AND `allow_http_fallback=False`), the
skill fails gracefully with `failure_reason=browser_runtime_missing` and never
crashes the eval.

Only http/https URLs on localhost / 127.0.0.1 / ::1 are allowed; anything else
is rejected with `failure_reason=url_not_allowed`.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

# Bootstrap repo root for consistency with the other candidates (not strictly
# required here, but keeps standalone execution predictable).
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


class BrowserError(Exception):
    """Raised for any non-crashing failure (resolved into failure_reason)."""


# --------------------------------------------------------------------------- #
# URL resolution + validation
# --------------------------------------------------------------------------- #

def _resolve_url(server_url, server_session_path):
    # Priority: explicit server_url > server_session_path's server_url.
    # (The orchestrator passes the blackboard/previous-skill server_url as
    #  server_url, so that tier is covered by the first branch.)
    if server_url:
        return server_url, None
    if server_session_path:
        p = Path(server_session_path)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                data = {}
            url = data.get("server_url") if isinstance(data, dict) else None
            if url:
                return url, None
    return None, "no_server_url"


def is_localhost_url(url: str) -> bool:
    try:
        u = urlparse(url)
    except Exception:  # noqa: BLE001
        return False
    if u.scheme not in ("http", "https"):
        return False
    host = (u.hostname or "").lower()
    return host in ("localhost", "127.0.0.1", "::1")


# --------------------------------------------------------------------------- #
# HTML snapshot parser
# --------------------------------------------------------------------------- #

class _SnapshotParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0
        self.text_parts: list[str] = []
        self.links: list[dict] = []
        self.buttons: list[dict] = []
        self.forms: list[dict] = []
        self._cur_a: dict | None = None
        self._cur_btn: dict | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "a":
            self._cur_a = {"href": a.get("href"), "text": ""}
        elif tag == "button":
            self._cur_btn = {"text": ""}
        elif tag == "input":
            itype = (a.get("type") or "text").lower()
            if itype in ("submit", "button", "reset"):
                self.buttons.append({"text": a.get("value") or itype, "type": itype})
        elif tag == "form":
            self.forms.append({"action": a.get("action"), "method": (a.get("method") or "get").lower()})

    def handle_startendtag(self, tag, attrs):
        # self-closing <input .../>
        if tag == "input":
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag == "a" and self._cur_a is not None:
            self.links.append({"href": self._cur_a["href"], "text": self._cur_a["text"].strip()})
            self._cur_a = None
        elif tag == "button" and self._cur_btn is not None:
            self.buttons.append({"text": self._cur_btn["text"].strip(), "type": "button"})
            self._cur_btn = None

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        self.text_parts.append(data)
        if self._cur_a is not None:
            self._cur_a["text"] += data
        if self._cur_btn is not None:
            self._cur_btn["text"] += data


def _parse_html(body: str) -> dict:
    parser = _SnapshotParser()
    try:
        parser.feed(body)
    except Exception:  # noqa: BLE001 - never let parsing crash the skill
        pass
    title = "".join(parser.title_parts).strip() or None
    text = re.sub(r"\s+", " ", " ".join(parser.text_parts)).strip()
    return {
        "title": title,
        "visible_text_preview": text[:300],
        "links": parser.links[:50],
        "buttons": parser.buttons[:50],
        "forms": parser.forms[:50],
        "counts": {
            "links": len(parser.links),
            "buttons": len(parser.buttons),
            "forms": len(parser.forms),
        },
    }


# --------------------------------------------------------------------------- #
# Engines
# --------------------------------------------------------------------------- #

def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def _load_with_playwright(url: str, timeout_sec: int, screenshot: bool) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page()
            resp = page.goto(url, timeout=timeout_sec * 1000, wait_until="load")
            status_code = resp.status if resp else None
            html = page.content()
            parsed = _parse_html(html)
            parsed["title"] = page.title() or parsed["title"]
            shot = page.screenshot() if screenshot else None
            return {"status_code": status_code, "engine": "playwright",
                    "parsed": parsed, "screenshot_bytes": shot}
        finally:
            browser.close()


def _load_with_http(url: str, timeout_sec: int) -> dict:
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "open-localhost-browser/1"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:  # noqa: S310 (localhost only)
        status_code = resp.getcode()
        charset = resp.headers.get_content_charset() or "utf-8"
        body = resp.read().decode(charset, errors="replace")
    parsed = _parse_html(body)
    return {"status_code": status_code, "engine": "http_fallback",
            "parsed": parsed, "screenshot_bytes": None}


# --------------------------------------------------------------------------- #
# Artifacts
# --------------------------------------------------------------------------- #

def _write_artifacts(artifacts_dir, result: dict, snapshot: dict | None,
                     screenshot_bytes: bytes | None) -> dict:
    if artifacts_dir:
        adir = Path(artifacts_dir)
        prefix = "artifacts"
    else:
        adir = Path(tempfile.mkdtemp(prefix="browser_artifacts_"))
        prefix = str(adir)
    adir.mkdir(parents=True, exist_ok=True)
    refs = {"result_ref": f"{prefix}/result.json", "page_snapshot_ref": None, "screenshot_ref": None}
    if snapshot is not None:
        refs["page_snapshot_ref"] = f"{prefix}/page_snapshot.json"
        (adir / "page_snapshot.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if screenshot_bytes:
        refs["screenshot_ref"] = f"{prefix}/screenshot.png"
        (adir / "screenshot.png").write_bytes(screenshot_bytes)
    (adir / "result.json").write_text(
        json.dumps({**result, **refs}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return refs


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def open_localhost_browser(server_url: str | None = None, server_session_path: str | None = None,
                           timeout_sec: int = 15, screenshot: bool = False,
                           allow_http_fallback: bool = True,
                           artifacts_dir: str | None = None,
                           browser_mode: str = "auto") -> dict:
    result: dict = {
        "status": "failed",          # loaded | failed
        "url": None,
        "title": None,
        "status_code": None,
        # browser runtime mode + capability flags (see ADR-013).
        "browser_mode": browser_mode,
        "engine": None,              # playwright | http_fallback | null
        "is_real_browser": False,
        "screenshot_supported": False,
        "js_supported": False,
        "console_supported": False,
        "browser_closed": False,
        "page_snapshot_ref": None,
        "result_ref": None,
        "screenshot_ref": None,
        "failure_reason": None,
        "error": None,
    }
    snapshot: dict | None = None
    screenshot_bytes: bytes | None = None

    # Resolve which engines may be used from the requested mode.
    #   auto          -> Playwright, then HTTP fallback (if allow_http_fallback)
    #   playwright     -> Playwright only; missing runtime -> browser_runtime_missing
    #   http_fallback  -> HTTP fallback only (force the degraded loader)
    if browser_mode == "playwright":
        try_playwright, try_fallback = True, False
    elif browser_mode == "http_fallback":
        try_playwright, try_fallback = False, True
    else:  # auto
        try_playwright, try_fallback = True, bool(allow_http_fallback)

    try:
        url, reason = _resolve_url(server_url, server_session_path)
        if reason:
            raise BrowserError(reason)
        result["url"] = url
        if not is_localhost_url(url):
            raise BrowserError("url_not_allowed")

        engine_result = None
        if try_playwright and _playwright_available():
            try:
                engine_result = _load_with_playwright(url, timeout_sec, screenshot)
            except Exception:  # noqa: BLE001 - degrade to the fallback, never crash
                engine_result = None
        if engine_result is None:
            if not try_fallback:
                raise BrowserError("browser_runtime_missing")
            try:
                engine_result = _load_with_http(url, timeout_sec)
            except Exception as exc:  # noqa: BLE001
                raise BrowserError(f"page_load_failed: {exc}")

        parsed = engine_result["parsed"]
        screenshot_bytes = engine_result.get("screenshot_bytes")
        engine = engine_result.get("engine")
        is_real = engine == "playwright"
        result["status"] = "loaded"
        result["status_code"] = engine_result.get("status_code")
        result["engine"] = engine
        result["is_real_browser"] = is_real
        # Only a real browser runtime supports screenshots, JS, and console.
        result["screenshot_supported"] = is_real
        result["js_supported"] = is_real
        result["console_supported"] = is_real
        result["title"] = parsed.get("title")
        snapshot = {"url": url, **parsed}

    except BrowserError as exc:
        result["failure_reason"] = str(exc)
        result["status"] = "failed"
    finally:
        # We use context managers / explicit close for every engine, so by here
        # no browser resource is left open. Record it for the verifier.
        result["browser_closed"] = True
        refs = _write_artifacts(artifacts_dir, result, snapshot, screenshot_bytes)
        result.update(refs)
        result["error"] = result["failure_reason"]

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default=None)
    parser.add_argument("--server-session-path", default=None)
    parser.add_argument("--timeout-sec", type=int, default=15)
    parser.add_argument("--screenshot", action="store_true")
    parser.add_argument("--no-http-fallback", action="store_true")
    parser.add_argument("--browser-mode", default="auto",
                        choices=["auto", "playwright", "http_fallback"])
    parser.add_argument("--artifacts-dir", default=None)
    args = parser.parse_args()
    print(json.dumps(
        open_localhost_browser(
            server_url=args.server_url,
            server_session_path=args.server_session_path,
            timeout_sec=args.timeout_sec,
            screenshot=args.screenshot,
            allow_http_fallback=not args.no_http_fallback,
            artifacts_dir=args.artifacts_dir,
            browser_mode=args.browser_mode,
        ),
        ensure_ascii=False,
        indent=2,
    ))
