"""Approved Review Package Import v0 — turn a review package into a NOT-APPROVED
fixture candidate (review/validation/approval-checklist only).

Takes an OpenAI (multi-step) review package and materializes a **fixture candidate**
for a human to review and (separately) approve. It is import-only and fail-closed:

  - **Dry-run by default.** Without `--write` nothing is created — it only validates
    the source plan and reports what WOULD be written.
  - **It NEVER writes an "approved" marker.** The generated `approval_checklist.md`
    is always `APPROVED_FOR_READONLY_EXECUTION: false` (NOT APPROVED). Approving stays
    a separate, human, manual step.
  - The plan must pass `PlanValidator`, contain ONLY the read-only allowlisted skills
    (`inspect_project`, `list_project_files`), and be all low-risk — else BLOCKED.
  - **No plan execution. No OpenAI / network call. No `.env` / password-file read.**
    All artifacts are redacted.

Output (under `fixtures/openai_planner/imported_review_package_<id>/`, gitignored):
  plan.json · plan_summary.md · approval_checklist.md · import_report.json · README.md

Exit codes:
  0  dry-run validated OK, OR (with --write) a fixture candidate was created
  1  blocked (invalid / non-allowlisted / not low-risk plan)
  2  fail-closed (review package / plan.json not found or unparseable)

Usage:
    .venv/bin/python scripts/import_review_package.py --dry-run --review-package <dir>
    .venv/bin/python scripts/import_review_package.py --write   --review-package <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import redact_text  # noqa: E402
from src.planner.plan_renderer import render_json, render_markdown  # noqa: E402
from src.planner.plan_validator import validate_plan  # noqa: E402
from src.planner.provider_planner import LivePlanError, parse_plan_from_text  # noqa: E402

# Read-only skills permitted in an imported candidate — kept in sync with
# src/planner/read_only_execution_gate.py READONLY_ALLOWLIST (NOT expanded here).
IMPORT_ALLOWLIST = ("inspect_project", "list_project_files")
FIXTURE_BASE = ROOT / "fixtures" / "openai_planner"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_plan_from_review_package(pkg_dir: Path):
    """Load + parse the plan.json from a review package (render_json format or raw).
    Raises LivePlanError/FileNotFoundError on a missing/unparseable plan."""
    plan_json = pkg_dir / "plan.json"
    data = json.loads(plan_json.read_text(encoding="utf-8"))
    plan_dict = data.get("plan", data) if isinstance(data, dict) else {}
    return parse_plan_from_text(json.dumps(plan_dict), plan_dict.get("goal", ""))


def candidate_id(plan) -> str:
    """Deterministic short id from the plan content (stable for the same plan)."""
    payload = json.dumps(plan.to_dict(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def assess_import(plan):
    """Return (ok, reasons). A candidate is importable only if the plan validates,
    uses ONLY the allowlisted read-only skills, and every step is low-risk."""
    validation = validate_plan(plan)
    reasons: list[str] = []
    if not validation.valid:
        reasons.append("plan_not_valid")
        reasons.extend(f"validation:{e}" for e in validation.errors)
    for s in plan.steps:
        if s.skill not in IMPORT_ALLOWLIST:
            reasons.append(f"non_allowlisted_skill:{s.id}:{s.skill}")
        if s.risk_level != "low":
            reasons.append(f"not_low_risk:{s.id}:{s.risk_level}")
    if not plan.steps:
        reasons.append("empty_plan")
    return (not reasons), reasons, validation


def _approval_md() -> str:
    # NEVER writes an approved marker — always NOT APPROVED.
    return (
        "# Approval Checklist (IMPORTED CANDIDATE — NOT APPROVED)\n\n"
        "**NOT APPROVED BY DEFAULT**\n\n"
        "**PLAN NOT EXECUTED**\n\n"
        "**HUMAN APPROVAL REQUIRED**\n\n"
        "- review_status: REVIEW-READY (imported)\n"
        "- APPROVED_FOR_READONLY_EXECUTION: false\n"
        "- reviewer: (none)\n\n"
        "## A human reviewer must confirm ALL before any read-only execution\n\n"
        "- [ ] I have read plan.json and plan_summary.md.\n"
        "- [ ] Every step uses only an allowlisted read-only skill "
        "(inspect_project / list_project_files).\n"
        "- [ ] Every step is risk_level low.\n"
        "- [ ] No secret appears in any artifact.\n"
        "- [ ] I understand the plan is NEVER auto-executed and NEVER auto-repaired.\n\n"
        "To approve, a human edits the line above to "
        "`APPROVED_FOR_READONLY_EXECUTION: true` and sets a non-empty `reviewer:`. The "
        "import tool itself NEVER writes the approved marker.\n"
    )


def _readme_md(cid: str, source: str) -> str:
    return (
        f"# Imported Review Package Candidate `{cid}`\n\n"
        f"- imported_from: {redact_text(source)}\n"
        "- status: **NOT APPROVED** (import-only; a human must approve separately)\n"
        "- plan: read-only, allowlisted (inspect_project / list_project_files), low-risk\n\n"
        "This is a **fixture candidate** for human review. It is never auto-approved, "
        "never executed, and never promoted by the import tool. To run it after a human "
        "sets `APPROVED_FOR_READONLY_EXECUTION: true` + a reviewer, use "
        "`scripts/run_openai_readonly_execution_gate.py` / "
        "`scripts/execute_openai_readonly_plan.py`.\n"
    )


def _write(out_dir: Path, name: str, text: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text(redact_text(text), encoding="utf-8")


def build_import_candidate(pkg_dir: Path, out_dir: Path, *, source_label: str) -> dict:
    """Validate + materialize a NOT-APPROVED fixture candidate. Returns a report dict.
    Writes nothing if the plan is not importable (caller decides)."""
    plan = load_plan_from_review_package(pkg_dir)
    ok, reasons, validation = assess_import(plan)
    cid = candidate_id(plan)
    plan_json = render_json(plan, validation)

    report = {
        "generated_at": _now_iso(),
        "source": source_label,
        "candidate_id": cid,
        "plan_valid": validation.valid,
        "skills": plan.skills,
        "import_allowlist": list(IMPORT_ALLOWLIST),
        "allowlisted_skills_only": all(s in IMPORT_ALLOWLIST for s in plan.skills) and bool(plan.skills),
        "low_risk_only": bool(plan.steps) and all(s.risk_level == "low" for s in plan.steps),
        "importable": ok,
        "block_reasons": [redact_text(r) for r in reasons],
        "approved_for_readonly_execution": False,   # NEVER approved by import
        "plan_executed": False,
        "auto_repair": False,
        "no_secret_in_plan": redact_text(plan_json) == plan_json,
    }
    if ok:
        _write(out_dir, "plan.json", plan_json)
        _write(out_dir, "plan_summary.md", render_markdown(plan, validation))
        _write(out_dir, "approval_checklist.md", _approval_md())
        _write(out_dir, "README.md", _readme_md(cid, source_label))
        safe = json.loads(redact_text(json.dumps(report, ensure_ascii=False)))
        _write(out_dir, "import_report.json",
               json.dumps(safe, ensure_ascii=False, indent=2) + "\n")
        report["fixture_candidate_dir"] = str(out_dir)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import a review package into a NOT-APPROVED fixture candidate (review-only).")
    parser.add_argument("--review-package", required=True,
                        help="path to a review package dir (must contain plan.json)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="validate only; create nothing (default behavior)")
    mode.add_argument("--write", action="store_true",
                      help="materialize the NOT-APPROVED fixture candidate")
    parser.add_argument("--out-base", default=str(FIXTURE_BASE),
                        help="base dir for imported_review_package_<id>/ (default fixtures/openai_planner)")
    args = parser.parse_args(argv)

    pkg = Path(args.review_package)
    if not (pkg / "plan.json").exists():
        print(f"[BLOCKED] review package plan.json not found under {pkg}", file=sys.stderr)
        print(json.dumps({"status": "BLOCKED", "reason": "plan.json not found"}, indent=2))
        return 2

    try:
        plan = load_plan_from_review_package(pkg)
    except (LivePlanError, Exception) as exc:  # noqa: BLE001
        print(f"[BLOCKED] could not parse the review package plan: {redact_text(str(exc))[:200]}",
              file=sys.stderr)
        print(json.dumps({"status": "BLOCKED",
                          "reason": redact_text(f"parse: {exc}")[:200]}, indent=2))
        return 2

    cid = candidate_id(plan)
    out_dir = Path(args.out_base) / f"imported_review_package_{cid}"

    ok, reasons, validation = assess_import(plan)
    summary = {
        "mode": "write" if args.write else "dry-run",
        "review_package": str(pkg),
        "candidate_id": cid,
        "would_write_to": str(out_dir),
        "plan_valid": validation.valid,
        "skills": plan.skills,
        "allowlisted_skills_only": all(s in IMPORT_ALLOWLIST for s in plan.skills) and bool(plan.skills),
        "low_risk_only": bool(plan.steps) and all(s.risk_level == "low" for s in plan.steps),
        "importable": ok,
        "block_reasons": [redact_text(r) for r in reasons],
        "approved_for_readonly_execution": False,
        "plan_executed": False,
    }

    if not ok:
        summary["status"] = "BLOCKED"
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        print(f"[BLOCKED] plan not importable: {'; '.join(reasons)}", file=sys.stderr)
        return 1

    if not args.write:
        summary["status"] = "DRY-RUN OK"
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        print("[DRY-RUN] plan validated + allowlisted + low-risk; nothing written. "
              "Use --write to create the NOT-APPROVED fixture candidate.", file=sys.stderr)
        return 0

    report = build_import_candidate(pkg, out_dir, source_label=str(pkg))
    summary["status"] = "WRITTEN"
    summary["fixture_candidate_dir"] = report.get("fixture_candidate_dir")
    print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
    print(f"[WRITTEN] NOT-APPROVED fixture candidate at {out_dir} (plan not executed, "
          "no approved marker, human approval required).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
