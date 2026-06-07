"""Read-only UI dashboard real-browser smoke gate.

Flow: generate snapshot -> validate dashboard -> start an IN-PROCESS localhost static
server -> open the dashboard in a REAL Playwright browser -> verify the read-only UI
-> teardown browser + server -> assert no lingering process.

It serves the dashboard from a `http.server` running in a background thread (no
spawned shell process, no raw shell) bound to 127.0.0.1, launches Chromium headless,
asserts the read-only properties, and tears everything down. It never installs
anything, makes no real API call, reads no secret, and adds no action surface.

    python scripts/run_dashboard_smoke.py --dry-run   # safe anywhere; runs nothing
    python scripts/run_dashboard_smoke.py             # only with Playwright + Chromium

Exit: 0 = smoke score 1.0; 1 = a criterion failed; 2 = runtime unavailable / blocked.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import importlib.util
import socket
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Reuse the Playwright runtime checks (no duplication).
_pw_spec = importlib.util.spec_from_file_location(
    "run_playwright_gate", ROOT / "scripts" / "run_playwright_gate.py")
_pwgate = importlib.util.module_from_spec(_pw_spec)
_pw_spec.loader.exec_module(_pwgate)

from src.llm.redaction import redact_text
from src.skills_runtime.simple_yaml import load_yaml

EVAL = ROOT / "evals" / "dashboard" / "ui_dashboard_readonly_smoke.yaml"
SERVE_ROOT = ROOT / "ui_dashboard"
PAGE_PATH = "/static/index.html"
INSTALL_HINT = "pip install playwright && playwright install chromium"

# Action verbs that must never appear as a clickable/trigger element on the page.
ACTION_WORDS = ("promote", "apply", "merge", "staging", "repair", "run ", "execute")


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # silence
        return


def _start_server() -> tuple[http.server.ThreadingHTTPServer, threading.Thread, int]:
    port = _free_port()
    handler = functools.partial(_QuietHandler, directory=str(SERVE_ROOT))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread, port


def _run_smoke(criteria: list[str]) -> dict:
    """Run the real-browser smoke. Returns {criterion: bool}."""
    from playwright.sync_api import sync_playwright

    ev = {c: False for c in criteria}

    # 1) snapshot + validation (pre-browser). Load both scripts by path (no package
    # import assumption), exactly like the Playwright-gate reuse above.
    def _load(stem: str):
        spec = importlib.util.spec_from_file_location(stem, ROOT / "scripts" / f"{stem}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    gen = _load("generate_dashboard_snapshot")
    vd = _load("validate_dashboard")

    ev["snapshot_generated"] = gen.main() == 0 and (
        ROOT / "ui_dashboard" / "data" / "dashboard_snapshot.json").exists()
    ev["dashboard_validated"] = vd.check(ROOT) == []

    httpd, thread, port = _start_server()
    base = f"http://127.0.0.1:{port}"
    external_requests: list[str] = []
    browser = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            def _on_request(req):
                host = req.url.split("/")[2] if "://" in req.url else ""
                if not (host.startswith("127.0.0.1") or host.startswith("localhost")):
                    external_requests.append(req.url)
            page.on("request", _on_request)

            resp = page.goto(base + PAGE_PATH, wait_until="networkidle", timeout=20000)
            ev["page_loaded"] = bool(resp and resp.ok)

            title = page.title()
            ev["title_visible"] = "dashboard" in title.lower()

            heading = (page.text_content("h1") or "")
            ev["heading_visible"] = "dashboard" in heading.lower()

            # snapshot-driven content
            lc = (page.text_content("#latest_checkpoint") or "")
            ev["latest_checkpoint_visible"] = "checkpoint-" in lc
            ps = (page.text_content("#phase_status") or "")
            ev["phase_status_visible"] = "phase" in ps.lower() and len(ps.strip()) > 0
            es = (page.text_content("#eval_status") or "")
            ev["eval_status_visible"] = len(es.strip()) > 0
            ga = (page.text_content("#generated_at") or "").strip()
            ev["snapshot_visible"] = ga not in ("", "—", "unavailable")

            # Dashboard Gate Status v0 — the new read-only status surfaces.
            prov = (page.text_content("#openai_provider_status") or "")
            ev["provider_status_visible"] = "openai" in prov.lower()
            pln = (page.text_content("#planner_live_status") or "")
            ev["planner_status_visible"] = "plan-only" in pln.lower()
            rx = (page.text_content("#readonly_execution_status") or "")
            ev["readonly_execution_status_visible"] = "read-only" in rx.lower() or "allowlisted" in rx.lower()
            al = (page.text_content("#readonly_allowlist") or "")
            ev["readonly_allowlist_visible"] = "inspect_project" in al
            gs = (page.text_content("#latest_gate_scores") or "")
            ev["gate_scores_visible"] = "openai_readonly_execution_gate" in gs
            bl = (page.text_content("#blocked_items") or "")
            ev["blocked_items_visible"] = "blocked" in bl.lower() or "stable promotion" in bl.lower()

            # read-only DOM assertions
            ev["no_button"] = page.eval_on_selector_all("button", "els => els.length") == 0
            ev["no_form"] = page.eval_on_selector_all("form", "els => els.length") == 0
            ev["no_onclick"] = page.eval_on_selector_all("[onclick]", "els => els.length") == 0
            # no method=post anywhere in the DOM
            post_count = page.evaluate(
                "() => document.documentElement.outerHTML.toLowerCase().split('method=\"post\"').length - 1")
            ev["no_post_action"] = post_count == 0

            body_text = (page.text_content("body") or "")
            ev["no_secret_in_body"] = redact_text(body_text) == body_text

            # no clickable action trigger: no button/form (covered) AND no anchor whose
            # text is an action verb pointing anywhere actionable
            anchors = page.eval_on_selector_all(
                "a", "els => els.map(e => (e.textContent||'').toLowerCase())")
            ev["no_action_trigger"] = (
                ev["no_button"] and ev["no_form"] and ev["no_onclick"]
                and not any(any(w in a for w in ACTION_WORDS) for a in anchors))

            context.close()
            browser.close()
            ev["browser_teardown"] = browser.is_connected() is False
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)

    ev["server_teardown"] = not thread.is_alive()
    ev["no_external_request"] = len(external_requests) == 0
    ev["no_lingering_process"] = (
        ev.get("browser_teardown", False) and ev.get("server_teardown", False))
    if external_requests:
        print(f"  [warn] external requests observed: {external_requests}", file=sys.stderr)
    return ev


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only dashboard real-browser smoke gate (no install).")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the checks/plan without launching a browser")
    args = parser.parse_args()

    task = load_yaml(EVAL)
    criteria = list(task.get("success_criteria") or [])

    print("Dashboard read-only real-browser smoke — ui_dashboard_readonly_smoke")
    print(f"  eval: {EVAL.relative_to(ROOT)}")
    print(f"  serves: {SERVE_ROOT.relative_to(ROOT)} (in-process localhost static server)")

    pkg = _pwgate.has_playwright_package()
    print(f"  [check] playwright python package: {'FOUND' if pkg else 'MISSING'}")

    if args.dry_run:
        print("  [check] chromium/browser runtime: (skipped in --dry-run)")
        print("  [plan] generate snapshot -> validate dashboard -> localhost static server")
        print("         -> open in real browser -> verify read-only UI -> teardown")
        print(f"  [plan] {len(criteria)} criteria: {', '.join(criteria)}")
        print(f"  [note] install in the target env (NOT done here): {INSTALL_HINT}")
        print("  [dry-run] no browser launched, no server started, nothing installed.")
        return 0

    if not pkg:
        print(f"[BLOCKED] Playwright not installed; smoke cannot run. {INSTALL_HINT}")
        return 2
    ok, detail = _pwgate.chromium_status()
    print(f"  [check] chromium/browser runtime: {'OK' if ok else 'MISSING'} ({detail})")
    if not ok:
        print(f"[BLOCKED] Chromium runtime unavailable; smoke cannot run. {INSTALL_HINT}")
        return 2

    ev = _run_smoke(criteria)
    passed = sum(1 for c in criteria if ev.get(c))
    score = round(passed / len(criteria), 4) if criteria else 0.0
    status = "PASS" if passed == len(criteria) else "FAIL"
    print(f"[{status}] ui_dashboard_readonly_smoke  score={score}")
    for c in criteria:
        print(f"  [{'x' if ev.get(c) else ' '}] {c}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
