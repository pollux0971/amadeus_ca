"""Review Package Approval Helper v0 — materialize a HUMAN-APPROVED read-only fixture.

Takes a **NOT-APPROVED** imported review candidate and, only with an explicit human
approval (`--approve` + a real `--reviewer`), writes an **approved** read-only fixture
the execution gate can run. It is approval-materialization only:

  - **Dry-run by default.** Without `--approve` nothing is written — it only validates.
  - **A real run requires `--approve` AND a non-empty `--reviewer`** that is not a
    placeholder (TBD / TODO / unknown / none). Otherwise it is rejected (fail closed).
  - The **source candidate must be NOT APPROVED** already (an
    `imported_review_package_*` dir or a committed example review package) — this tool
    never re-approves an already-approved fixture and never auto-approves.
  - The plan must pass `PlanValidator`, use ONLY `inspect_project` +
    `list_project_files`, and be all low-risk — else BLOCKED.
  - It writes a **line-anchored** `APPROVED_FOR_READONLY_EXECUTION: true` marker so the
    gate recognizes it; the approval is granted by the named human reviewer, not the
    model or the planner.
  - **No plan execution. No OpenAI / network call. No `.env` / password-file read.**
    All artifacts redacted.

Output (under `fixtures/openai_planner/approved_imported_<id>/`, gitignored):
  plan.json · approval_checklist.md · approval_report.json · README.md

Exit codes:
  0  dry-run validated OK, OR (with --approve + reviewer) an approved fixture was written
  1  blocked (no --approve / bad reviewer / already approved / invalid / non-allowlisted)
  2  fail-closed (candidate not found / not an allowed source / unparseable plan)

Usage:
    .venv/bin/python scripts/approve_review_candidate.py --dry-run \
        --candidate reports/openai_multistep_plan_review_v0/example --output-id smoke
    .venv/bin/python scripts/approve_review_candidate.py --approve --reviewer "alice" \
        --candidate fixtures/openai_planner/imported_review_package_<id> --output-id myrun
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import redact_text  # noqa: E402
from src.planner.plan_renderer import render_json  # noqa: E402
from src.planner.read_only_execution_gate import (  # noqa: E402
    APPROVAL_MARKER_RE, parse_approval,
)

# Reuse the import helpers (plan loader + read-only allowlist + risk assessment).
_imp_spec = importlib.util.spec_from_file_location(
    "import_review_package", ROOT / "scripts" / "import_review_package.py")
imp = importlib.util.module_from_spec(_imp_spec)
_imp_spec.loader.exec_module(imp)

APPROVE_ALLOWLIST = imp.IMPORT_ALLOWLIST  # ("inspect_project", "list_project_files")
FIXTURE_BASE = ROOT / "fixtures" / "openai_planner"
# Committed example review packages are acceptable NOT-APPROVED candidates (test data).
EXAMPLE_CANDIDATES = (
    ROOT / "reports" / "openai_multistep_plan_review_v0" / "example",
    ROOT / "reports" / "openai_plan_review_v0" / "example",
)
# Placeholder reviewer names that are NOT a real human sign-off.
BAD_REVIEWERS = {"", "tbd", "todo", "unknown", "(none)", "none", "n/a", "na", "xxx"}
# A safe id (so the output dir name can never escape the fixtures base).
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_allowed_candidate(path: Path) -> bool:
    """A candidate must be an imported_review_package_* dir under
    fixtures/openai_planner/ OR a committed example review package."""
    try:
        rp = path.resolve()
    except OSError:
        return False
    if rp in (e.resolve() for e in EXAMPLE_CANDIDATES):
        return True
    try:
        rel = rp.relative_to(FIXTURE_BASE.resolve())
    except ValueError:
        return False
    return rel.parts and rel.parts[0].startswith("imported_review_package_")


def validate_reviewer(reviewer: str) -> tuple[bool, str]:
    r = (reviewer or "").strip()
    if r.lower() in BAD_REVIEWERS:
        return False, "reviewer is empty or a placeholder (TBD/TODO/unknown/none)"
    return True, r


def _approval_md(reviewer: str) -> str:
    # The marker is a STANDALONE line so the gate's line-anchored parse recognizes it.
    return (
        "# Approval Checklist (HUMAN-APPROVED read-only fixture)\n\n"
        "**HUMAN-APPROVED for read-only execution by the named reviewer below.**\n\n"
        "APPROVED_FOR_READONLY_EXECUTION: true\n\n"
        f"reviewer: {redact_text(reviewer)}\n\n"
        "## Confirmed by the human reviewer\n\n"
        "- [x] I read plan.json and confirmed it is read-only and low-risk.\n"
        "- [x] Every step uses only an allowlisted read-only skill "
        "(inspect_project / list_project_files).\n"
        "- [x] No secret appears in any artifact.\n"
        "- [x] This authorizes ONLY allowlisted read-only execution — never patch / "
        "browser / console / server / repair / apply / merge / staging / promotion.\n"
    )


def _readme_md(out_id: str, source: str, reviewer: str) -> str:
    return (
        f"# Approved Imported Fixture `{out_id}`\n\n"
        f"- approved_from: {redact_text(source)}\n"
        f"- reviewer: {redact_text(reviewer)}\n"
        "- status: **APPROVED** for read-only execution (allowlisted: inspect_project / "
        "list_project_files; low-risk only)\n\n"
        "Human-approved by the named reviewer. The plan is still NEVER auto-executed "
        "and NEVER auto-repaired. To run it, use "
        "`scripts/run_openai_readonly_execution_gate.py` / "
        "`scripts/execute_openai_readonly_plan.py`.\n"
    )


def _write(out_dir: Path, name: str, text: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text(redact_text(text), encoding="utf-8")


def build_approved_fixture(candidate_dir: Path, out_dir: Path, *, reviewer: str,
                           source_label: str) -> dict:
    """Validate + materialize an APPROVED read-only fixture from a NOT-APPROVED
    candidate. Returns a report dict. Caller guarantees authorization."""
    plan = imp.load_plan_from_review_package(candidate_dir)
    ok, reasons, validation = imp.assess_import(plan)
    plan_json = render_json(plan, validation)

    report = {
        "generated_at": _now_iso(),
        "source": source_label,
        "reviewer": reviewer,
        "plan_valid": validation.valid,
        "skills": plan.skills,
        "approve_allowlist": list(APPROVE_ALLOWLIST),
        "allowlisted_skills_only": all(s in APPROVE_ALLOWLIST for s in plan.skills) and bool(plan.skills),
        "low_risk_only": bool(plan.steps) and all(s.risk_level == "low" for s in plan.steps),
        "approvable": ok,
        "block_reasons": [redact_text(r) for r in reasons],
        "approved_for_readonly_execution": True,
        "plan_executed": False,
        "auto_repair": False,
        "no_secret_in_plan": redact_text(plan_json) == plan_json,
    }
    if ok:
        chk = _approval_md(reviewer)
        report["approval_marker_line_anchored"] = bool(APPROVAL_MARKER_RE.search(chk))
        _write(out_dir, "plan.json", plan_json)
        _write(out_dir, "approval_checklist.md", chk)
        _write(out_dir, "README.md", _readme_md(out_dir.name, source_label, reviewer))
        safe = json.loads(redact_text(json.dumps(report, ensure_ascii=False)))
        _write(out_dir, "approval_report.json",
               json.dumps(safe, ensure_ascii=False, indent=2) + "\n")
        report["approved_fixture_dir"] = str(out_dir)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize a HUMAN-APPROVED read-only fixture from a NOT-APPROVED candidate.")
    parser.add_argument("--candidate", required=True,
                        help="path to a NOT-APPROVED candidate (imported_review_package_* or example)")
    parser.add_argument("--output-id", required=True, help="id for approved_imported_<id>/")
    parser.add_argument("--reviewer", default="", help="non-empty human reviewer name (required to --approve)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="validate only; write nothing (default)")
    mode.add_argument("--approve", action="store_true", help="write the approved fixture (needs --reviewer)")
    parser.add_argument("--out-base", default=str(FIXTURE_BASE))
    args = parser.parse_args(argv)

    cand = Path(args.candidate)
    out_id = args.output_id

    summary = {
        "mode": "approve" if args.approve else "dry-run",
        "candidate": str(cand),
        "output_id": out_id,
        "plan_executed": False,
        "real_api_called": False,
    }

    # Fail closed: source allow + id shape + plan present.
    if not SAFE_ID_RE.match(out_id):
        summary["status"] = "BLOCKED"
        summary["reason"] = "invalid --output-id (use [A-Za-z0-9._-])"
        print(json.dumps(summary, indent=2)); print("[BLOCKED] invalid --output-id.", file=sys.stderr)
        return 2
    if not is_allowed_candidate(cand):
        summary["status"] = "BLOCKED"
        summary["reason"] = "candidate is not an imported_review_package_* dir or a committed example"
        print(json.dumps(summary, indent=2))
        print("[BLOCKED] candidate must be under fixtures/openai_planner/imported_review_package_* "
              "or a committed example review package.", file=sys.stderr)
        return 2
    if not (cand / "plan.json").exists():
        summary["status"] = "BLOCKED"
        summary["reason"] = "candidate plan.json not found"
        print(json.dumps(summary, indent=2)); print("[BLOCKED] candidate plan.json not found.", file=sys.stderr)
        return 2

    # The candidate must currently be NOT APPROVED (never re-approve / auto-approve).
    chk_path = cand / "approval_checklist.md"
    candidate_was_not_approved = True
    if chk_path.exists():
        candidate_was_not_approved = parse_approval(chk_path.read_text(encoding="utf-8")).approved_marker is False
    summary["candidate_was_not_approved"] = candidate_was_not_approved
    if not candidate_was_not_approved:
        summary["status"] = "BLOCKED"
        summary["reason"] = "candidate is already APPROVED (refusing to re-approve)"
        print(json.dumps(summary, indent=2)); print("[BLOCKED] candidate is already approved.", file=sys.stderr)
        return 1

    # Validate the plan (valid + allowlisted + low-risk).
    try:
        plan = imp.load_plan_from_review_package(cand)
    except Exception as exc:  # noqa: BLE001
        summary["status"] = "BLOCKED"
        summary["reason"] = redact_text(f"parse: {exc}")[:200]
        print(json.dumps(summary, indent=2)); print("[BLOCKED] could not parse the plan.", file=sys.stderr)
        return 2
    ok, reasons, validation = imp.assess_import(plan)
    summary.update({
        "plan_valid": validation.valid,
        "skills": plan.skills,
        "allowlisted_skills_only": all(s in APPROVE_ALLOWLIST for s in plan.skills) and bool(plan.skills),
        "low_risk_only": bool(plan.steps) and all(s.risk_level == "low" for s in plan.steps),
        "approvable": ok,
        "block_reasons": [redact_text(r) for r in reasons],
    })
    if not ok:
        summary["status"] = "BLOCKED"
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        print(f"[BLOCKED] plan not approvable: {'; '.join(reasons)}", file=sys.stderr)
        return 1

    # Reviewer is required for an actual approval.
    rev_ok, reviewer = validate_reviewer(args.reviewer)
    summary["reviewer_ok"] = rev_ok

    out_dir = Path(args.out_base) / f"approved_imported_{out_id}"
    summary["would_write_to"] = str(out_dir)

    if not args.approve:
        # Dry-run: validate everything (incl. that a reviewer WOULD be required) but
        # write nothing.
        summary["status"] = "DRY-RUN OK"
        summary["note"] = "approval requires --approve + a non-empty, non-placeholder --reviewer"
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        print("[DRY-RUN] candidate validated; NOT written. Use --approve --reviewer <name> "
              "to materialize the approved fixture.", file=sys.stderr)
        return 0

    if not rev_ok:
        summary["status"] = "BLOCKED"
        summary["reason"] = "approval requires a non-empty, non-placeholder --reviewer"
        print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
        print("[BLOCKED] --approve requires a real --reviewer (not TBD/TODO/unknown/none).",
              file=sys.stderr)
        return 1

    report = build_approved_fixture(cand, out_dir, reviewer=reviewer, source_label=str(cand))
    summary["status"] = "APPROVED"
    summary["approved_fixture_dir"] = report.get("approved_fixture_dir")
    summary["approval_marker_line_anchored"] = report.get("approval_marker_line_anchored")
    print(redact_text(json.dumps(summary, ensure_ascii=False, indent=2)))
    print(f"[APPROVED] human-approved read-only fixture written to {out_dir} "
          f"(reviewer={redact_text(reviewer)}; plan not executed).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
