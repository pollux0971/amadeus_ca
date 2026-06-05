"""Candidate read_browser_console v1 — REAL Playwright browser console only.

Collects genuine browser console logs (and uncaught page errors) from a live
localhost page using a real Playwright browser. It NEVER uses an HTTP fallback
and NEVER fabricates a console — if a real browser runtime is unavailable it
fails gracefully with a clear failure_reason. It does not start or kill the
server; the server lifecycle stays with start_local_server + the orchestrator's
end-of-run teardown.

Runtime policy:
  - browser_mode defaults to "playwright"; a missing browser_mode is treated as
    "playwright".
  - browser_mode == "http_fallback"  -> failure_reason=http_fallback_not_allowed.
  - Playwright package / browser runtime missing -> failure_reason=browser_runtime_missing.
  - No fallback console is ever produced.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


class ConsoleError(Exception):
    """Raised for any non-crashing failure (resolved into failure_reason)."""


# --------------------------------------------------------------------------- #
# URL resolution + validation
# --------------------------------------------------------------------------- #

def _resolve_url(server_url, server_session_path):
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
    return None, "missing_server_url"


def is_localhost_url(url: str) -> bool:
    try:
        u = urlparse(url)
    except Exception:  # noqa: BLE001
        return False
    if u.scheme not in ("http", "https"):
        return False
    return (u.hostname or "").lower() in ("localhost", "127.0.0.1", "::1")


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------- #
# Console classification
# --------------------------------------------------------------------------- #

def classify_console_type(msg_type: str) -> str:
    t = (msg_type or "").lower()
    if t == "error":
        return "error"
    if t in ("warning", "warn"):
        return "warning"
    if t == "info":
        return "info"
    # log / debug / dir / table / trace / ... -> debug bucket
    return "debug"


def _empty_counts() -> dict:
    return {"fatal": 0, "error": 0, "warning": 0, "info": 0, "debug": 0, "total": 0}


# --------------------------------------------------------------------------- #
# Artifacts
# --------------------------------------------------------------------------- #

def _write_artifacts(artifacts_dir, result: dict, console_log: dict | None,
                     snapshot: dict | None, screenshot_bytes: bytes | None) -> dict:
    if artifacts_dir:
        adir = Path(artifacts_dir)
        prefix = "artifacts"
    else:
        adir = Path(tempfile.mkdtemp(prefix="console_artifacts_"))
        prefix = str(adir)
    adir.mkdir(parents=True, exist_ok=True)
    refs = {
        "result_ref": f"{prefix}/result.json",
        "console_log_ref": None,
        "page_snapshot_ref": None,
        "screenshot_ref": None,
    }
    if console_log is not None:
        refs["console_log_ref"] = f"{prefix}/console_log.json"
        (adir / "console_log.json").write_text(
            json.dumps(console_log, ensure_ascii=False, indent=2), encoding="utf-8")
    if snapshot is not None:
        refs["page_snapshot_ref"] = f"{prefix}/page_snapshot.json"
        (adir / "page_snapshot.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    if screenshot_bytes:
        refs["screenshot_ref"] = f"{prefix}/screenshot.png"
        (adir / "screenshot.png").write_bytes(screenshot_bytes)
    (adir / "result.json").write_text(
        json.dumps({**result, **refs}, ensure_ascii=False, indent=2), encoding="utf-8")
    return refs


# --------------------------------------------------------------------------- #
# Real-browser collection
# --------------------------------------------------------------------------- #

def _collect_with_playwright(url, timeout_sec, wait_after_load_ms, screenshot):
    from playwright.sync_api import sync_playwright

    entries: list[dict] = []
    page_errors: list[dict] = []
    seq = {"n": 0}

    def _next() -> int:
        i = seq["n"]
        seq["n"] += 1
        return i

    title = None
    status_code = None
    shot = None
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = None
        try:
            context = browser.new_context()
            page = context.new_page()

            def on_console(msg):
                try:
                    loc = msg.location
                except Exception:  # noqa: BLE001
                    loc = None
                entries.append({
                    "seq": _next(),
                    "type": msg.type,
                    "category": classify_console_type(msg.type),
                    "text": msg.text,
                    "location": loc,
                    "ts": time.time(),
                })

            def on_pageerror(err):
                page_errors.append({
                    "seq": _next(),
                    "message": getattr(err, "message", None) or str(err),
                    "stack": getattr(err, "stack", None),
                    "ts": time.time(),
                })

            page.on("console", on_console)
            page.on("pageerror", on_pageerror)

            resp = page.goto(url, timeout=timeout_sec * 1000, wait_until="load")
            status_code = resp.status if resp else None
            if wait_after_load_ms:
                page.wait_for_timeout(wait_after_load_ms)
            title = page.title()
            if screenshot:
                shot = page.screenshot()
        finally:
            if context is not None:
                context.close()
            browser.close()

    return {
        "title": title,
        "status_code": status_code,
        "entries": entries,
        "page_errors": page_errors,
        "screenshot_bytes": shot,
    }


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def read_browser_console(server_url: str | None = None, server_session_path: str | None = None,
                         browser_mode: str | None = "playwright", timeout_sec: int = 15,
                         wait_after_load_ms: int = 300, fail_on_console_error: bool = False,
                         screenshot: bool = False, artifacts_dir: str | None = None) -> dict:
    result: dict = {
        "status": "failed",            # collected | failed
        "engine": None,                # playwright on success
        "is_real_browser": False,
        "console_supported": False,
        "browser_mode": browser_mode if browser_mode else "playwright",
        "url": None,
        "title": None,
        "status_code": None,
        "console_counts": _empty_counts(),
        "has_fatal_console_error": False,
        "has_console_error": False,
        # Back-compat fields (so existing evals that check console_errors /
        # fatal_error_count keep working); always present.
        "console_errors": [],
        "fatal_error_count": 0,
        "summary": "",
        "browser_closed": False,
        "console_log_ref": None,
        "result_ref": None,
        "page_snapshot_ref": None,
        "screenshot_ref": None,
        "failure_reason": None,
        "error": None,
    }

    console_log = None
    snapshot = None
    screenshot_bytes = None
    mode = (browser_mode or "playwright").lower()

    try:
        # Strict runtime policy — no http_fallback, no fake console.
        if mode == "http_fallback":
            raise ConsoleError("http_fallback_not_allowed")
        if mode != "playwright":
            # Any non-playwright, non-fallback mode is treated as requiring a real
            # browser too; an unknown mode is not a license to fabricate a console.
            mode = "playwright"

        # Input validation first (reported regardless of runtime availability).
        url, reason = _resolve_url(server_url, server_session_path)
        if reason:
            raise ConsoleError(reason)
        result["url"] = url
        if not is_localhost_url(url):
            raise ConsoleError("url_not_allowed")

        # Then require a real browser runtime — never fabricate a console.
        if not _playwright_available():
            raise ConsoleError("browser_runtime_missing")

        try:
            collected = _collect_with_playwright(url, timeout_sec, wait_after_load_ms, screenshot)
        except Exception as exc:  # noqa: BLE001 - launch/runtime problems are graceful failures
            raise ConsoleError(f"browser_runtime_missing: {type(exc).__name__}: {exc}")

        entries = collected["entries"]
        page_errors = collected["page_errors"]
        title = collected["title"]
        screenshot_bytes = collected["screenshot_bytes"]

        counts = _empty_counts()
        for e in entries:
            counts[e["category"]] = counts.get(e["category"], 0) + 1
        counts["fatal"] = len(page_errors)
        counts["total"] = len(entries) + len(page_errors)

        error_entries = [e for e in entries if e["category"] == "error"]
        result.update({
            "engine": "playwright",
            "is_real_browser": True,
            "console_supported": True,
            "title": title,
            "status_code": collected["status_code"],
            "console_counts": counts,
            "has_fatal_console_error": counts["fatal"] > 0,
            "has_console_error": counts["error"] > 0,
            # back-compat
            "console_errors": [{"type": "error", "text": e["text"]} for e in error_entries],
            "fatal_error_count": counts["fatal"],
            "summary": (f"{counts['error']} error(s), {counts['warning']} warning(s), "
                        f"{counts['fatal']} page error(s)"),
        })

        console_log = {
            "url": url,
            "title": title,
            "entries": entries,
            "page_errors": page_errors,
            "counts": counts,
            "collected_at": time.time(),
        }
        snapshot = {"url": url, "title": title, "counts": counts}

        if fail_on_console_error and (result["has_console_error"] or result["has_fatal_console_error"]):
            result["status"] = "failed"
            result["failure_reason"] = "console_error_present"
        else:
            result["status"] = "collected"

    except ConsoleError as exc:
        result["failure_reason"] = str(exc)
        result["status"] = "failed"
    finally:
        # We never leave a browser open (every engine path uses context managers /
        # explicit close), and we never touch the server.
        result["browser_closed"] = True
        refs = _write_artifacts(artifacts_dir, result, console_log, snapshot, screenshot_bytes)
        result.update(refs)
        result["error"] = result["failure_reason"]

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default=None)
    parser.add_argument("--server-session-path", default=None)
    parser.add_argument("--browser-mode", default="playwright")
    parser.add_argument("--timeout-sec", type=int, default=15)
    parser.add_argument("--wait-after-load-ms", type=int, default=300)
    parser.add_argument("--fail-on-console-error", action="store_true")
    parser.add_argument("--screenshot", action="store_true")
    parser.add_argument("--artifacts-dir", default=None)
    args = parser.parse_args()
    print(json.dumps(
        read_browser_console(
            server_url=args.server_url,
            server_session_path=args.server_session_path,
            browser_mode=args.browser_mode,
            timeout_sec=args.timeout_sec,
            wait_after_load_ms=args.wait_after_load_ms,
            fail_on_console_error=args.fail_on_console_error,
            screenshot=args.screenshot,
            artifacts_dir=args.artifacts_dir,
        ),
        ensure_ascii=False, indent=2,
    ))
