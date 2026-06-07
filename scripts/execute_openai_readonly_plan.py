"""Execute an APPROVED read-only plan — human-gated, allowlisted, read-only only.

This runs a plan through the Read-Only Plan Execution Gate
(`src/planner/read_only_execution_gate.py`). It is **dry-run by default** and
fail-closed. A REAL execution happens ONLY when ALL hold:

  - `--approved` is passed (and not `--dry-run`), AND
  - the approval checklist contains `APPROVED_FOR_READONLY_EXECUTION: true`, AND
  - a non-empty reviewer is present (from the checklist or `--reviewer`), AND
  - the plan passes `PlanValidator`, AND
  - every step uses an allowlisted, read-only skill (v0: `inspect_project`).

It refuses patch / server / browser / console / repair / apply / merge / staging /
promotion / raw-shell skills outright. It does NOT call OpenAI (it consumes an
already-approved, redacted plan — e.g. Story 1's review package / fixture). It never
replans, never auto-repairs, never starts a shell, and never reads a secret. The
`project_dir` it inspects is a VETTED operator input — never the model's plan inputs,
browser content, or run traces. Every result/report is redacted.

Exit codes:
  0  dry-run report, OR a real read-only execution succeeded
  1  blocked (authorization failed / plan not read-only-executable)
  2  fail-closed (could not load the plan / approval)

Usage:
    .venv/bin/python scripts/execute_openai_readonly_plan.py --dry-run
    .venv/bin/python scripts/execute_openai_readonly_plan.py \
        --review-package fixtures/openai_planner/approved_readonly_plan \
        --approved --reviewer "alice" --project-dir .
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import redact_text  # noqa: E402
from src.planner.provider_planner import LivePlanError, parse_plan_from_text  # noqa: E402
from src.planner.read_only_execution_gate import (  # noqa: E402
    ApprovalRecord, ReadOnlyExecutionError, authorize, execute_readonly_plan,
    parse_approval, validate_readonly_plan,
)

DEFAULT_REVIEW_PACKAGE = ROOT / "fixtures" / "openai_planner" / "approved_readonly_plan"
DEFAULT_OUTPUT = ROOT / "runs" / "openai_readonly_plan_execution"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_plan(plan_json_path: Path):
    data = json.loads(plan_json_path.read_text(encoding="utf-8"))
    plan_dict = data.get("plan", data) if isinstance(data, dict) else {}
    return parse_plan_from_text(json.dumps(plan_dict), plan_dict.get("goal", ""))


def _write(out_dir: Path, name: str, text: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / name
    p.write_text(redact_text(text), encoding="utf-8")
    return p


def _report(out_dir: Path, summary: dict) -> Path:
    safe = json.loads(redact_text(json.dumps(summary, ensure_ascii=False)))
    return _write(out_dir, "execution_report.json",
                  json.dumps(safe, ensure_ascii=False, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute an approved read-only plan (dry-run default; allowlisted read-only only).")
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--review-package", default="",
                     help="dir with plan.json + approval_checklist.md (default: the approved fixture)")
    src.add_argument("--plan-json", default="", help="a plan.json to execute (no checklist)")
    parser.add_argument("--approved", action="store_true",
                        help="operator opt-in: authorize a REAL read-only execution")
    parser.add_argument("--reviewer", default="", help="reviewer name (overrides the checklist)")
    parser.add_argument("--project-dir", default=str(ROOT),
                        help="VETTED directory for inspect_project (operator input; default: repo root)")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate + report what WOULD run; never executes (default behavior)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    out_dir = Path(args.output)
    # Resolve the plan + approval source.
    pkg = Path(args.review_package) if args.review_package else (
        None if args.plan_json else DEFAULT_REVIEW_PACKAGE)
    plan_json_path = Path(args.plan_json) if args.plan_json else (
        (pkg / "plan.json") if pkg else None)
    checklist_path = (pkg / "approval_checklist.md") if pkg else None

    summary: dict = {
        "generated_at": _now_iso(),
        "real_api_called": False,            # this script never calls OpenAI
        "auto_repair": False,
        "replanned": False,
        "project_dir": str(args.project_dir),
        "read_only_allowlist": ["inspect_project"],
    }

    if not plan_json_path or not plan_json_path.exists():
        summary["status"] = "BLOCKED"
        summary["reason"] = f"plan.json not found ({plan_json_path})"
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        _report(out_dir, summary)
        print("[BLOCKED] could not load a plan.", file=sys.stderr)
        return 2

    try:
        plan = _load_plan(plan_json_path)
    except (LivePlanError, Exception) as exc:  # noqa: BLE001
        summary["status"] = "BLOCKED"
        summary["reason"] = redact_text(f"could not parse plan: {exc}")[:300]
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        _report(out_dir, summary)
        print("[BLOCKED] could not parse the plan.", file=sys.stderr)
        return 2

    approval = ApprovalRecord()
    if checklist_path and checklist_path.exists():
        approval = parse_approval(checklist_path.read_text(encoding="utf-8"))
    if args.reviewer:
        approval.reviewer = args.reviewer

    gate = validate_readonly_plan(plan)
    auth = authorize(plan, approval, approved=args.approved)
    summary.update({
        "plan_readonly_executable": gate.ok,
        "gate_errors": [redact_text(e) for e in gate.errors],
        "allowed_steps": gate.allowed_steps,
        "approval_marker_present": approval.approved_marker,
        "reviewer_present": approval.reviewer_ok,
        "approved_flag": bool(args.approved),
        "authorized": auth.ok,
    })

    real_exec = bool(args.approved) and not args.dry_run
    if not real_exec:
        summary["mode"] = "dry-run"
        summary["plan_executed"] = False
        summary["status"] = "DRY-RUN OK" if gate.ok else "DRY-RUN (plan not executable)"
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        rpt = _report(out_dir, summary)
        print(f"[REPORT] {rpt}", file=sys.stderr)
        print("[DRY-RUN] gate evaluated; nothing executed (read-only execution needs "
              "--approved + checklist marker + reviewer + a valid allowlisted plan).",
              file=sys.stderr)
        return 0

    # REAL read-only execution — fail closed unless fully authorized.
    summary["mode"] = "execute"
    if not auth.ok:
        summary["plan_executed"] = False
        summary["status"] = "BLOCKED"
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        _report(out_dir, summary)
        print(f"[BLOCKED] not authorized: {'; '.join(auth.errors)}", file=sys.stderr)
        return 1

    try:
        result = execute_readonly_plan(plan, approval, approved=args.approved,
                                       project_dir=args.project_dir)
    except ReadOnlyExecutionError as exc:
        summary["plan_executed"] = False
        summary["status"] = "BLOCKED"
        summary["reason"] = redact_text(str(exc))[:300]
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        _report(out_dir, summary)
        print(f"[BLOCKED] {redact_text(str(exc))[:200]}", file=sys.stderr)
        return 1

    summary["plan_executed"] = True
    summary["status"] = "EXECUTED"
    summary["execution"] = result
    print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
    rpt = _report(out_dir, summary)
    print(f"[REPORT] {rpt}", file=sys.stderr)
    print("[EXECUTED] approved read-only plan ran allowlisted skills only; no shell, "
          "no auto-repair, no replan. Results are redacted.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
