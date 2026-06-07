"""Run the OpenAI Read-Only Execution Gate over the APPROVED fixture (re-runnable).

This is the operator entry point for the read-only execution eval gate. It drives the
human-approved Read-Only Plan Execution Gate (`src/planner/read_only_execution_gate.py`)
over the committed APPROVED, redacted plan fixture and writes a redacted gate report.

Hard boundaries:
  - **Dry-run by default.** Without `--execute` nothing runs — it only validates the
    fixture (approval marker / reviewer / PlanValidator / read-only allowlist).
  - **`--execute` runs ONLY allowlisted read-only skills (v0: inspect_project).**
  - **It only accepts a plan under `fixtures/openai_planner/`** (a vetted, redacted,
    committed fixture). Any other path is refused (fail closed).
  - **No OpenAI / network call.** It consumes an already-approved plan; it never calls
    a provider and never reads an env key.
  - It never reads `password_and_api.txt` or `.env`, never patches / servers / browses
    / repairs / applies / merges / stages / promotes, never runs a shell, never
    replans, never auto-repairs. The `project_dir` is a vetted operator input.
  - Outputs `gate_report.json` / `gate_report.md`, both redacted.

Exit codes:
  0  dry-run validated OK, OR an approved read-only execution succeeded
  1  blocked (authorization failed / plan not read-only-executable)
  2  fail-closed (fixture missing / path outside fixtures/openai_planner/ / parse error)

Usage:
    .venv/bin/python scripts/run_openai_readonly_execution_gate.py --dry-run
    .venv/bin/python scripts/run_openai_readonly_execution_gate.py --execute
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
from src.planner.plan_validator import validate_plan  # noqa: E402
from src.planner.provider_planner import parse_plan_from_text  # noqa: E402
from src.planner.read_only_execution_gate import (  # noqa: E402
    READONLY_ALLOWLIST, ApprovalRecord, ReadOnlyExecutionError, authorize,
    execute_readonly_plan, parse_approval, validate_readonly_plan,
)

# The ONLY directory a plan fixture may live under (vetted, redacted, committed).
FIXTURE_ROOT = ROOT / "fixtures" / "openai_planner"
DEFAULT_FIXTURE = FIXTURE_ROOT / "approved_readonly_plan"
DEFAULT_OUTPUT = ROOT / "runs" / "openai_readonly_execution_gate"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _within_fixture_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(FIXTURE_ROOT.resolve())
        return True
    except ValueError:
        return False


def _load_plan(plan_json_path: Path):
    data = json.loads(plan_json_path.read_text(encoding="utf-8"))
    plan_dict = data.get("plan", data) if isinstance(data, dict) else {}
    return parse_plan_from_text(json.dumps(plan_dict), plan_dict.get("goal", ""))


def _write(out_dir: Path, name: str, text: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / name
    p.write_text(redact_text(text), encoding="utf-8")
    return p


def _report_md(report: dict) -> str:
    lines = ["# OpenAI Read-Only Execution Gate Report", "",
             f"- generated_at: {report.get('generated_at')}",
             f"- mode: {report.get('mode')}",
             f"- status: {report.get('status')}",
             f"- fixture: {report.get('fixture')}",
             f"- real_api_called: {report.get('real_api_called')}",
             f"- read_only: {report.get('read_only')}",
             f"- authorized: {report.get('authorized')}",
             f"- approval_marker_present: {report.get('approval_marker_present')}",
             f"- reviewer_present: {report.get('reviewer_present')}",
             f"- plan_valid: {report.get('plan_valid')}",
             f"- executed_once: {report.get('executed_once')}",
             f"- skills: {', '.join(report.get('skills') or []) or '(none)'}",
             f"- read_only_allowlist: {', '.join(report.get('read_only_allowlist') or [])}",
             "",
             "> Read-only gate — only allowlisted read-only skills run; no patch / "
             "browser / console / server / repair / apply / merge / staging / promotion "
             "/ raw shell; no OpenAI call; no auto-repair. All output is redacted.",
             ""]
    return "\n".join(lines)


def _emit(out_dir: Path, report: dict) -> None:
    safe = json.loads(redact_text(json.dumps(report, ensure_ascii=False)))
    print(redact_text(json.dumps(safe, ensure_ascii=False, indent=2)))
    _write(out_dir, "gate_report.json", json.dumps(safe, ensure_ascii=False, indent=2) + "\n")
    _write(out_dir, "gate_report.md", _report_md(safe))
    print(f"[REPORT] {out_dir}/gate_report.json", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the OpenAI read-only execution gate over the approved fixture.")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE),
                        help="approved plan fixture dir (MUST be under fixtures/openai_planner/)")
    parser.add_argument("--project-dir", default=str(ROOT),
                        help="VETTED directory for inspect_project (operator input)")
    parser.add_argument("--dry-run", action="store_true", help="validate only; execute nothing (default)")
    parser.add_argument("--execute", action="store_true", help="run the approved read-only plan once")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    out_dir = Path(args.output)
    fixture_dir = Path(args.fixture)
    report = {
        "generated_at": _now_iso(),
        "real_api_called": False,
        "auto_repair": False,
        "replanned": False,
        "read_only": True,
        "fixture": str(fixture_dir),
        "project_dir": str(args.project_dir),
        "read_only_allowlist": list(READONLY_ALLOWLIST),
    }

    # Fail closed: only a fixture under fixtures/openai_planner/ is allowed.
    if not _within_fixture_root(fixture_dir):
        report["status"] = "BLOCKED"
        report["reason"] = "fixture path is outside fixtures/openai_planner/ (refused)"
        _emit(out_dir, report)
        print("[BLOCKED] fixture path must be under fixtures/openai_planner/.", file=sys.stderr)
        return 2

    plan_json = fixture_dir / "plan.json"
    checklist = fixture_dir / "approval_checklist.md"
    if not plan_json.exists():
        report["status"] = "BLOCKED"
        report["reason"] = f"plan.json not found ({plan_json})"
        _emit(out_dir, report)
        print("[BLOCKED] approved plan.json not found.", file=sys.stderr)
        return 2

    try:
        plan = _load_plan(plan_json)
    except Exception as exc:  # noqa: BLE001
        report["status"] = "BLOCKED"
        report["reason"] = redact_text(f"could not parse plan: {exc}")[:200]
        _emit(out_dir, report)
        print("[BLOCKED] could not parse the approved plan.", file=sys.stderr)
        return 2

    approval = parse_approval(checklist.read_text(encoding="utf-8")) if checklist.exists() \
        else ApprovalRecord()
    validation = validate_plan(plan)
    gate = validate_readonly_plan(plan)
    auth = authorize(plan, approval, approved=True)

    report.update({
        "skills": plan.skills,
        "approval_marker_present": approval.approved_marker,
        "reviewer_present": approval.reviewer_ok,
        "plan_valid": validation.valid,
        "plan_readonly_executable": gate.ok,
        "authorized": auth.ok,
        "gate_errors": [redact_text(e) for e in gate.errors],
    })

    if not args.execute:
        report["mode"] = "dry-run"
        report["status"] = "DRY-RUN OK" if gate.ok else "DRY-RUN (plan not executable)"
        report["executed_once"] = False
        _emit(out_dir, report)
        print("[DRY-RUN] fixture validated; nothing executed (use --execute to run "
              "the approved read-only plan).", file=sys.stderr)
        return 0

    report["mode"] = "execute"
    if not auth.ok:
        report["status"] = "BLOCKED"
        report["executed_once"] = False
        _emit(out_dir, report)
        print(f"[BLOCKED] not authorized: {'; '.join(auth.errors)}", file=sys.stderr)
        return 1

    try:
        result = execute_readonly_plan(plan, approval, approved=True,
                                       project_dir=str(args.project_dir))
    except ReadOnlyExecutionError as exc:
        report["status"] = "BLOCKED"
        report["executed_once"] = False
        report["reason"] = redact_text(str(exc))[:200]
        _emit(out_dir, report)
        print(f"[BLOCKED] {redact_text(str(exc))[:200]}", file=sys.stderr)
        return 1

    report["status"] = "EXECUTED"
    report["executed_once"] = result.get("steps_executed") == len(plan.steps)
    report["execution"] = result
    _emit(out_dir, report)
    print("[EXECUTED] approved read-only plan ran allowlisted skills only (no OpenAI "
          "call, no shell, no auto-repair). Results redacted.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
