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
    # Real-browser smoke gate (story_ui_dashboard_smoke_v0).
    "evals/dashboard/ui_dashboard_readonly_smoke.yaml",
    "scripts/run_dashboard_smoke.py",
    "reports/story_ui_dashboard_smoke_v0/README.md",
]

# The smoke eval must declare these read-only / teardown criteria.
REQUIRED_SMOKE_CRITERIA = [
    "page_loaded", "snapshot_visible", "no_button", "no_form", "no_onclick",
    "no_post_action", "no_external_request", "no_secret_in_body",
    "no_action_trigger", "browser_teardown", "server_teardown", "no_lingering_process",
    # Dashboard Gate Status v0 — the new read-only status surfaces must be visible.
    "provider_status_visible", "planner_status_visible",
    "readonly_execution_status_visible", "readonly_allowlist_visible",
    "gate_scores_visible", "blocked_items_visible",
]

REQUIRED_SNAPSHOT_KEYS = [
    "latest_checkpoint", "phase_status", "candidate_status", "eval_status",
    "epic_story_status", "safety_invariants", "links_to_reports", "generated_at",
    # Dashboard Gate Status v0 keys.
    "openai_provider_status", "planner_live_status", "readonly_execution_status",
    "readonly_allowlist", "latest_gate_scores", "blocked_items",
]

# The dashboard may only DISPLAY read-only skills in the allowlist (status only — it
# never executes anything). Anything outside this set is a hard error.
READONLY_DISPLAY_ALLOWLIST = {"inspect_project", "list_project_files"}
FORBIDDEN_ALLOWLIST_SKILLS = {
    "patch_file_and_run_tests", "start_local_server", "open_localhost_browser",
    "read_browser_console", "repair", "apply", "merge", "staging_promote", "staging",
    "promote", "promotion", "raw_shell", "direct_command", "exec", "eval", "bash",
}

# Required dashboard UI section ids (read-only status surfaces).
REQUIRED_UI_SECTION_IDS = [
    "openai_provider_status", "planner_live_status", "readonly_execution_status",
    "readonly_allowlist", "latest_gate_scores", "blocked_items",
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
    # The displayed read-only allowlist may ONLY list read-only skills, never a
    # forbidden action skill.
    allowlist = data.get("readonly_allowlist")
    if allowlist is not None:
        if not isinstance(allowlist, list):
            errors.append(f"{rel}: readonly_allowlist must be a list")
        else:
            for skill in allowlist:
                if skill in FORBIDDEN_ALLOWLIST_SKILLS:
                    errors.append(f"{rel}: readonly_allowlist contains a forbidden skill {skill!r}")
                elif skill not in READONLY_DISPLAY_ALLOWLIST:
                    errors.append(f"{rel}: readonly_allowlist has a non-read-only skill {skill!r}")
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
        html = index.read_text(encoding="utf-8")
        low = html.lower()
        for pat in ("<form", "method=\"post\"", "onclick=", "formaction"):
            if pat in low:
                errors.append(f"index.html contains forbidden pattern: {pat!r}")
        # The read-only status surfaces must each have a section anchor.
        for sid in REQUIRED_UI_SECTION_IDS:
            if f'id="{sid}"' not in html:
                errors.append(f"index.html missing read-only status section id: {sid!r}")

    # app.js must render the new status sections (read-only, via textContent).
    appjs2 = root / "ui_dashboard" / "static" / "app.js"
    if appjs2.exists():
        ajs = appjs2.read_text(encoding="utf-8")
        for sid in REQUIRED_UI_SECTION_IDS:
            if sid not in ajs:
                errors.append(f"app.js does not render status section: {sid!r}")

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

    # Smoke gate: eval declares the read-only/teardown criteria; runner is shell-free
    # and offers a --dry-run.
    smoke_eval = root / "evals" / "dashboard" / "ui_dashboard_readonly_smoke.yaml"
    if smoke_eval.exists():
        low = smoke_eval.read_text(encoding="utf-8").lower()
        for c in REQUIRED_SMOKE_CRITERIA:
            if c not in low:
                errors.append(f"ui_dashboard_readonly_smoke.yaml missing criterion: {c!r}")
    runner = root / "scripts" / "run_dashboard_smoke.py"
    if runner.exists():
        src = runner.read_text(encoding="utf-8")
        if "shell=True" in src or "os.system" in src or "subprocess" in src:
            errors.append("run_dashboard_smoke.py runs a shell/subprocess")
        if "--dry-run" not in src:
            errors.append("run_dashboard_smoke.py lacks a --dry-run mode")
        if "http.server" not in src:
            errors.append("run_dashboard_smoke.py does not use an in-process http.server")

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
