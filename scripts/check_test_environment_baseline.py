"""Test environment baseline checker — report-only, no install, no network.

Reports the differences between the **system Python** and the project **`.venv`**
that matter for testing (see `docs/test_environment_baseline.md`), so a
Playwright-environment gap is never misread as a regression.

What it checks (and ONLY reports — it changes nothing):
  - whether `.venv/bin/python` exists (the real-browser verification path),
  - whether the Playwright package is importable (current interpreter, and the
    `.venv` interpreter via a lightweight subprocess probe),
  - whether a Chromium runtime is usable in the current interpreter,
  - whether a bare `python` is on PATH — **a missing `python` is a WARNING, never a
    failure**,
  - the known environment-gap tests that fail ONLY on `.venv` (Playwright present).

Hard guarantees:
  - **No network download. No package install. No environment mutation.**
  - **No secret read** — it reads no `.env`, no `password_and_api.txt`, no key value;
    it prints no environment-variable values.

Exit codes:
  0  baseline reported (default; env gaps are reported as WARNING/BLOCKED notes)
  2  ONLY with `--require-real-browser` when the real-browser path is unavailable
     (i.e. a context that documents the real-browser gate as mandatory)

Usage:
    .venv/bin/python scripts/check_test_environment_baseline.py
    .venv/bin/python scripts/check_test_environment_baseline.py --json
    .venv/bin/python scripts/check_test_environment_baseline.py --require-real-browser
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The known environment-gap tests: they assume a Playwright-ABSENT environment, so
# they pass on system Python and fail ONLY on the .venv (Playwright present). Kept in
# sync with docs/test_environment_baseline.md. NOT regressions.
KNOWN_ENV_GAP_TESTS = [
    "tests/unit/test_browser_keep_alive_e2e.py::test_browser_keep_alive_smoke_scores_1_and_no_lingering",
    "tests/unit/test_full_browser_gate_script.py::test_missing_prereqs_block_with_exit_2",
]

# Commands that need the .venv real-browser runtime (documented in the baseline doc).
REAL_BROWSER_COMMANDS = [
    ".venv/bin/python scripts/run_playwright_gate.py",
    ".venv/bin/python scripts/run_full_browser_gate.py",
    ".venv/bin/python scripts/run_dashboard_smoke.py",
]


def _venv_python(root: Path) -> Path:
    return root / ".venv" / "bin" / "python"


def _has_playwright_current() -> bool:
    return importlib.util.find_spec("playwright") is not None


def _chromium_status_current() -> tuple[bool, str]:
    """(ok, detail) for the CURRENT interpreter. Never launches a page; only resolves
    the Chromium executable path. Safe / no network."""
    if not _has_playwright_current():
        return False, "playwright package not importable in this interpreter"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            path = pw.chromium.executable_path
        ok = bool(path) and Path(path).exists()
        return ok, ("chromium runtime present" if ok else "chromium executable not found")
    except Exception as exc:  # noqa: BLE001 - report only, never raise
        return False, f"chromium check failed: {exc}"


def _probe_venv_playwright(root: Path) -> tuple[bool, str]:
    """Probe the .venv interpreter for the Playwright package via a tiny subprocess.
    Imports nothing in THIS process; installs nothing; no network."""
    vp = _venv_python(root)
    if not vp.exists():
        return False, ".venv/bin/python not found"
    # Are we ALREADY running inside this .venv? Compare sys.prefix (a venv's python
    # resolves to the same base interpreter as the system one, so resolve() would
    # misfire — use the prefix instead).
    if Path(sys.prefix).resolve() == (root / ".venv").resolve():
        return _has_playwright_current(), "current interpreter is the .venv"
    try:
        proc = subprocess.run(
            [str(vp), "-c", "import importlib.util,sys;"
             "sys.exit(0 if importlib.util.find_spec('playwright') else 1)"],
            capture_output=True, text=True, timeout=30)
        return proc.returncode == 0, ("playwright importable in .venv"
                                      if proc.returncode == 0 else "playwright not in .venv")
    except Exception as exc:  # noqa: BLE001
        return False, f"venv probe failed: {exc}"


def gather(root: Path) -> dict:
    venv_py = _venv_python(root)
    venv_exists = venv_py.exists()
    pw_current = _has_playwright_current()
    chromium_ok, chromium_detail = _chromium_status_current()
    venv_pw_ok, venv_pw_detail = _probe_venv_playwright(root)
    python_on_path = shutil.which("python")

    real_browser_available = bool(venv_exists and (venv_pw_ok or (pw_current and chromium_ok)))

    return {
        "root": str(root),
        "current_interpreter": sys.executable,
        "current_has_playwright": pw_current,
        "current_chromium_ok": chromium_ok,
        "current_chromium_detail": chromium_detail,
        "venv_python": str(venv_py),
        "venv_python_exists": venv_exists,
        "venv_has_playwright": venv_pw_ok,
        "venv_playwright_detail": venv_pw_detail,
        # presence/path only — never a value, never a secret
        "python_on_path": bool(python_on_path),
        "python_on_path_location": python_on_path or "",
        "real_browser_path_available": real_browser_available,
        "real_browser_path": str(venv_py),
        "known_env_gap_tests": list(KNOWN_ENV_GAP_TESTS),
        "real_browser_commands": list(REAL_BROWSER_COMMANDS),
    }


def warnings_for(summary: dict) -> list[str]:
    warns: list[str] = []
    if not summary["python_on_path"]:
        warns.append("`python` is not on PATH — use an explicit interpreter "
                     "(.venv/bin/python or /usr/bin/python3). WARNING only, not a failure.")
    if not summary["venv_python_exists"]:
        warns.append("`.venv/bin/python` not found — the real-browser verification path "
                     "is unavailable; real-browser gates are BLOCKED until the .venv exists.")
    if not summary["real_browser_path_available"]:
        warns.append("Playwright/Chromium real-browser runtime not available — real-browser "
                     "gates degrade to http_fallback (NOT a real browser); run them on .venv.")
    return warns


def render_text(summary: dict, warns: list[str]) -> str:
    lines = [
        "Test Environment Baseline",
        f"  root: {summary['root']}",
        f"  current interpreter: {summary['current_interpreter']}",
        f"    [check] playwright package: {'FOUND' if summary['current_has_playwright'] else 'MISSING'}",
        f"    [check] chromium runtime: {'OK' if summary['current_chromium_ok'] else 'MISSING'} "
        f"({summary['current_chromium_detail']})",
        f"  .venv python: {summary['venv_python']} "
        f"({'EXISTS' if summary['venv_python_exists'] else 'MISSING'})",
        f"    [check] playwright in .venv: {'FOUND' if summary['venv_has_playwright'] else 'MISSING'} "
        f"({summary['venv_playwright_detail']})",
        f"  python on PATH: {'YES' if summary['python_on_path'] else 'NO (warning only)'}"
        + (f" ({summary['python_on_path_location']})" if summary['python_on_path'] else ""),
        f"  real-browser path available: {'YES' if summary['real_browser_path_available'] else 'NO'} "
        f"-> {summary['real_browser_path']}",
        "  real-browser commands (use .venv/bin/python):",
    ]
    for c in summary["real_browser_commands"]:
        lines.append(f"    - {c}")
    lines.append("  known environment-gap tests (fail ONLY on .venv; NOT regressions):")
    for t in summary["known_env_gap_tests"]:
        lines.append(f"    - {t}")
    if warns:
        lines.append("  WARNINGS:")
        for w in warns:
            lines.append(f"    [WARN] {w}")
    else:
        lines.append("  [OK] no environment warnings")
    lines.append("  [note] this checker installs nothing, downloads nothing, reads no secret.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report the test-environment baseline (no install, no network, no secret).")
    parser.add_argument("--json", action="store_true", help="emit the summary as JSON")
    parser.add_argument("--require-real-browser", action="store_true",
                        help="exit 2 if the .venv real-browser path is unavailable "
                             "(for contexts where the real-browser gate is mandatory)")
    args = parser.parse_args(argv)

    summary = gather(ROOT)
    warns = warnings_for(summary)

    if args.json:
        print(json.dumps({"summary": summary, "warnings": warns}, ensure_ascii=False, indent=2))
    else:
        print(render_text(summary, warns))

    # A missing bare `python` is ALWAYS only a warning — never affects the exit code.
    if args.require_real_browser and not summary["real_browser_path_available"]:
        print("[BLOCKED] --require-real-browser: the .venv real-browser path is unavailable.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
