"""Playwright real-browser gate runner for open_localhost_browser_v1.

It ONLY runs the real-browser gate eval, and ONLY when a Playwright runtime is
actually available. It never installs anything and never changes any candidate
status.

Behavior:
  1. Check the `playwright` Python package is importable.
  2. Check a Chromium/browser runtime is usable.
  3. If either is missing → print a clear message and exit code 2.
  4. If both present → run the gate eval via scripts/run_eval.py.

Use `--dry-run` to print the checks/plan without launching a browser or running
the eval.

    python scripts/run_playwright_gate.py --dry-run   # safe anywhere
    python scripts/run_playwright_gate.py             # only with Playwright+Chromium

Do NOT run the non-dry-run form unless Playwright + Chromium are installed.
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_EVAL = ROOT / "evals" / "browser" / "open_localhost_playwright_required_smoke.yaml"
RUN_EVAL = ROOT / "scripts" / "run_eval.py"

# Operator action printed as guidance ONLY. This script never executes it.
INSTALL_HINT = "pip install playwright && playwright install chromium"


def has_playwright_package() -> bool:
    return importlib.util.find_spec("playwright") is not None


def chromium_status() -> tuple[bool, str]:
    """Return (ok, detail). Only call when the package is present."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        return False, f"playwright import failed: {exc}"
    try:
        with sync_playwright() as pw:
            path = pw.chromium.executable_path
        ok = bool(path) and Path(path).exists()
        return ok, (str(path) if ok else "chromium executable not found")
    except Exception as exc:  # noqa: BLE001
        return False, f"chromium check failed: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Playwright real-browser gate (no install).")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the checks/plan without launching a browser or running the eval")
    args = parser.parse_args()

    print("Playwright real-browser gate — open_localhost_browser_v1")
    print(f"  gate eval: {GATE_EVAL.relative_to(ROOT)}")

    pkg = has_playwright_package()
    print(f"  [check] playwright python package: {'FOUND' if pkg else 'MISSING'}")

    if args.dry_run:
        print("  [check] chromium/browser runtime: (skipped in --dry-run)")
        print("  [plan] when both are present this gate will run:")
        print(f"           {sys.executable} {RUN_EVAL.relative_to(ROOT)} --task {GATE_EVAL.relative_to(ROOT)}")
        print(f"  [note] to install in the target env (NOT done here): {INSTALL_HINT}")
        print("  [dry-run] no browser launched, no eval executed, nothing installed.")
        return 0

    if not pkg:
        print("[BLOCKED] Playwright is not installed; the real-browser gate cannot run.")
        print(f"          Install it in the target environment first: {INSTALL_HINT}")
        print("          This gate does NOT auto-install anything.")
        return 2

    ok, detail = chromium_status()
    print(f"  [check] chromium/browser runtime: {'OK' if ok else 'MISSING'} ({detail})")
    if not ok:
        print("[BLOCKED] Chromium browser runtime is unavailable; the gate cannot run.")
        print(f"          Install it in the target environment first: {INSTALL_HINT}")
        print("          This gate does NOT auto-install anything.")
        return 2

    print("[OK] Playwright + Chromium present. Running the real-browser gate eval...")
    proc = subprocess.run([sys.executable, str(RUN_EVAL), "--task", str(GATE_EVAL)])
    if proc.returncode == 0:
        print("[PASS] real-browser gate eval scored 1.0. open_localhost_browser_v1 "
              "may now be considered for staging-ready (update its candidate status).")
    else:
        print("[FAIL] real-browser gate eval did not reach 1.0; keep open_localhost_browser_v1 at dev.")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
