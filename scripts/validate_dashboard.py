"""Validate the read-only UI dashboard skeleton (story_ui_dashboard_skeleton_v0).

Checks that the skeleton exists, is read-only (no action execution / raw shell / API
/ secret), and that the snapshot(s) carry the required keys and no secret.

Usable standalone (`python scripts/validate_dashboard.py`) and imported by
`scripts/validate_workflows.py` via `_module_errors(root, "validate_dashboard")`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_FALLBACK = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "ui_dashboard/README.md",
    "ui_dashboard/static/index.html",
    "ui_dashboard/static/app.js",
    "ui_dashboard/static/styles.css",
    "ui_dashboard/data/dashboard_snapshot.example.json",
    "scripts/generate_dashboard_snapshot.py",
    "reports/story_ui_dashboard_skeleton_v0/README.md",
]

REQUIRED_SNAPSHOT_KEYS = [
    "latest_checkpoint", "phase_status", "candidate_status", "eval_status",
    "epic_story_status", "safety_invariants", "links_to_reports", "generated_at",
]

# Patterns that would mean the static UI can execute an action / leak a secret.
FORBIDDEN_JS_PATTERNS = [
    "eval(", "innerhtml", "document.write", "xmlhttprequest", "new function(",
    "method: \"post\"", "method: 'post'", "fetch(\"http", "fetch('http",
    "ws://", "wss://",
]

# Secret-looking content must never appear in committed/generated dashboard artifacts.
def _contains_secret(root: Path, rel: str) -> bool:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from src.llm.redaction import redact_text
    text = (root / rel).read_text(encoding="utf-8")
    return redact_text(text) != text


def _check_snapshot(root: Path, rel: str, errors: list[str]) -> None:
    p = root / rel
    if not p.exists():
        return
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{rel}: invalid JSON ({exc})")
        return
    for key in REQUIRED_SNAPSHOT_KEYS:
        if key not in data:
            errors.append(f"{rel}: missing key {key!r}")
    if _contains_secret(root, rel):
        errors.append(f"{rel}: contains a secret-looking value")
    # Must not embed raw runs trace / api key markers.
    low = p.read_text(encoding="utf-8").lower()
    for bad in ("api_key", "authorization:", "trace.jsonl\":"):
        if bad in low:
            errors.append(f"{rel}: forbidden content {bad!r}")


def check(root: Path | None = None) -> list[str]:
    root = root or ROOT_FALLBACK
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing dashboard path: {rel}")

    # README must state the read-only boundaries.
    readme = root / "ui_dashboard" / "README.md"
    if readme.exists():
        low = readme.read_text(encoding="utf-8").lower()
        for phrase in ("read-only", "no action execution", "no raw shell",
                       "no api call", "no secret"):
            if phrase not in low:
                errors.append(f"ui_dashboard/README.md missing phrase: {phrase!r}")

    # app.js must be read-only: no execution / external-network / innerHTML / eval.
    appjs = root / "ui_dashboard" / "static" / "app.js"
    if appjs.exists():
        low = appjs.read_text(encoding="utf-8").lower()
        for pat in FORBIDDEN_JS_PATTERNS:
            if pat in low:
                errors.append(f"app.js contains forbidden pattern: {pat!r}")

    # index.html must not contain a form/POST or action button.
    index = root / "ui_dashboard" / "static" / "index.html"
    if index.exists():
        low = index.read_text(encoding="utf-8").lower()
        for pat in ("<form", "method=\"post\"", "onclick=", "formaction"):
            if pat in low:
                errors.append(f"index.html contains forbidden pattern: {pat!r}")

    # generator must not read .env / password / runs raw, and must refuse on secret.
    gen = root / "scripts" / "generate_dashboard_snapshot.py"
    if gen.exists():
        src = gen.read_text(encoding="utf-8")
        if "shell=True" in src or "os.system" in src or "subprocess" in src:
            errors.append("generate_dashboard_snapshot.py runs a shell/subprocess")
        if "refusing to write" not in src.lower() and "blocked" not in src.lower():
            errors.append("generate_dashboard_snapshot.py lacks a refuse-on-secret guard")

    # Snapshots: example always; generated if present.
    _check_snapshot(root, "ui_dashboard/data/dashboard_snapshot.example.json", errors)
    if (root / "ui_dashboard/data/dashboard_snapshot.json").exists():
        _check_snapshot(root, "ui_dashboard/data/dashboard_snapshot.json", errors)

    return errors


def main() -> int:
    errors = check(ROOT_FALLBACK)
    if errors:
        print("[FAIL] dashboard validation:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[PASS] dashboard skeleton is read-only and the snapshot is valid (no secret)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
