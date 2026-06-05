"""Full real-browser end-to-end gate runner (draft chain).

Runs `evals/browser/full_browser_vite_login_bug_e2e.yaml` ONLY when every
prerequisite is met. It never installs anything and never changes candidate
status.

Prerequisites:
  1. Playwright Python package is importable.
  2. A Chromium/browser runtime is usable.
  3. open_localhost_browser's real-browser Playwright gate has PASSED
     (a passing `open_localhost_playwright_required_smoke` run exists with
     `task_success` and `browser_is_real`).
  4. A `read_browser_console` candidate exists and forces a real browser.

If any prerequisite is unmet → print all unmet reasons and exit code 2.

    python scripts/run_full_browser_gate.py --dry-run   # safe anywhere
    python scripts/run_full_browser_gate.py             # only when ALL prereqs met

Do NOT run the non-dry-run form until the prerequisites above are real.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL_EVAL = ROOT / "evals" / "browser" / "full_browser_vite_login_bug_e2e.yaml"
PLAYWRIGHT_GATE_EVAL_ID = "open_localhost_playwright_required_smoke"
RUN_EVAL = ROOT / "scripts" / "run_eval.py"
INSTALL_HINT = "pip install playwright && playwright install chromium"

# Reuse the Playwright gate's runtime checks (no duplication).
_pw_spec = importlib.util.spec_from_file_location(
    "run_playwright_gate", ROOT / "scripts" / "run_playwright_gate.py")
_pwgate = importlib.util.module_from_spec(_pw_spec)
_pw_spec.loader.exec_module(_pwgate)


def playwright_gate_passed(root: Path) -> tuple[bool, str]:
    runs = root / "runs"
    if not runs.exists():
        return False, "no runs/ directory; gate eval has not been run"
    for score_path in sorted(runs.glob("*/score.json")):
        try:
            score = json.loads(score_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if score.get("task_id") != PLAYWRIGHT_GATE_EVAL_ID:
            continue
        if score.get("task_success") and (score.get("metrics") or {}).get("browser_is_real"):
            return True, f"passing run: {score_path.parent.name}"
    return False, "no passing real-browser gate run found (run scripts/run_playwright_gate.py)"


def console_candidate_exists(root: Path) -> bool:
    base = root / "harnesses" / "candidates"
    if not base.exists():
        return False
    return any(p.exists() for p in base.glob("read_browser_console*/candidate.yaml"))


def evaluate_prerequisites(root: Path) -> list[dict]:
    pw = _pwgate.has_playwright_package()
    prereqs = [{"name": "playwright_python_package", "met": pw,
                "detail": "FOUND" if pw else f"MISSING ({INSTALL_HINT})"}]

    if pw:
        ok, detail = _pwgate.chromium_status()
    else:
        ok, detail = False, "skipped (playwright package missing)"
    prereqs.append({"name": "chromium_runtime", "met": ok, "detail": detail})

    gate_ok, gate_detail = playwright_gate_passed(root)
    prereqs.append({"name": "open_localhost_browser_real_browser_gate_passed",
                    "met": gate_ok, "detail": gate_detail})

    cc = console_candidate_exists(root)
    prereqs.append({"name": "read_browser_console_candidate_exists", "met": cc,
                    "detail": "FOUND" if cc else "MISSING (read_browser_console is blocked)"})
    return prereqs


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full real-browser e2e gate (no install).")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the blocked prerequisites without launching a browser or running the eval")
    args = parser.parse_args()

    print("Full real-browser e2e gate — full_browser_vite_login_bug_e2e (draft)")
    print(f"  eval: {FULL_EVAL.relative_to(ROOT)}")

    prereqs = evaluate_prerequisites(ROOT)
    for p in prereqs:
        print(f"  [check] {p['name']}: {'MET' if p['met'] else 'UNMET'} ({p['detail']})")
    unmet = [p for p in prereqs if not p["met"]]

    if args.dry_run:
        print("  [dry-run] blocked prerequisites:")
        for p in (unmet or [{"name": "(none)"}]):
            print(f"             - {p['name']}")
        print("  [plan] when ALL are met this gate will run:")
        print(f"           {sys.executable} {RUN_EVAL.relative_to(ROOT)} --task {FULL_EVAL.relative_to(ROOT)}")
        print("  [dry-run] no browser launched, no eval executed, nothing installed.")
        return 0

    if unmet:
        print("[BLOCKED] full real-browser gate cannot run; unmet prerequisites:")
        for p in unmet:
            print(f"            - {p['name']}: {p['detail']}")
        print("          This gate does NOT auto-install or start anything.")
        return 2

    print("[OK] all prerequisites met. Running the full real-browser e2e...")
    proc = subprocess.run([sys.executable, str(RUN_EVAL), "--task", str(FULL_EVAL)])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
