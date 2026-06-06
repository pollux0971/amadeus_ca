"""repair_apply.py — apply an APPROVED repair proposal into an apply workspace.

Approved Patch Application v0 is WORKSPACE-ONLY. This script reads a repair
proposal workspace, revalidates the proposal, checks the human approval marker +
reviewer, and (only with explicit `--approved`) materializes the approved changes
into an apply workspace. It NEVER modifies a real target file, a stable skill, the
safety gate, or the promotion policy, and it NEVER promotes or merges.

It can run ONLY a fixed, hardcoded allowlist of test commands (never derived from
the proposal), and only when explicitly asked with `--run-tests`.

    # safe preview — validates + prints the plan, creates no workspace
    python scripts/repair_apply.py \
        --proposal-workspace fixtures/repair/fake_approved_proposal_workspace --dry-run

    # apply to a candidate apply workspace (requires explicit --approved)
    python scripts/repair_apply.py \
        --proposal-workspace fixtures/repair/fake_approved_proposal_workspace \
        --approved --apply-id fake_apply_smoke
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.repair.patch_application import (
    ALLOWLISTED_TEST_COMMANDS, DEFAULT_APPLY_BASE, apply_proposal,
    load_proposal_workspace,
)
from src.repair.apply_validator import parse_approval, validate_for_apply
from src.repair.proposal_validator import validate_proposal
from src.repair.apply_report import render_apply_report


def _run_allowlisted_tests() -> dict:
    """Run ONLY the fixed allowlist (never proposal-derived). Opt-in via --run-tests."""
    import subprocess  # local import: only used on explicit --run-tests
    results = []
    for cmd in ALLOWLISTED_TEST_COMMANDS:
        # cmd is from the hardcoded constant only — split into argv, no shell.
        argv = cmd.split()
        if argv and argv[0] == "python":
            argv[0] = sys.executable
        proc = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True)
        results.append({"command": cmd, "ok": proc.returncode == 0, "exit": proc.returncode})
    return {"executed": True, "commands": list(ALLOWLISTED_TEST_COMMANDS), "results": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply an APPROVED repair proposal into a candidate apply workspace (v0).")
    parser.add_argument("--proposal-workspace", required=True,
                        help="Path to a repair proposal workspace (with approval_checklist.md).")
    parser.add_argument("--apply-id", default="repair_apply",
                        help="Identifier for the apply workspace.")
    parser.add_argument("--output", default=str(ROOT / DEFAULT_APPLY_BASE),
                        help="Base dir for the apply workspace.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate + print the plan; create no apply workspace.")
    parser.add_argument("--approved", action="store_true",
                        help="Explicit operator confirmation required to create the apply workspace.")
    parser.add_argument("--run-tests", action="store_true",
                        help="Also run the FIXED test allowlist (never proposal-derived).")
    args = parser.parse_args(argv)

    ws = Path(args.proposal_workspace)
    if not ws.is_absolute():
        ws = ROOT / args.proposal_workspace
    if not ws.exists():
        print(f"[FAIL] proposal workspace not found: {args.proposal_workspace}", file=sys.stderr)
        return 2

    proposal, analysis, approval_text = load_proposal_workspace(ws)
    approval = parse_approval(approval_text)
    revalidation = validate_proposal(proposal)
    apply_validation = validate_for_apply(proposal, approval)

    # Always print the plan (redacted) — what WOULD be applied.
    print(f"# Repair Apply Plan — proposal `{proposal.id}`")
    print(f"- proposal revalidated: {revalidation.valid}")
    print(f"- approval marker: {approval.approved}  reviewer: "
          f"{'set' if approval.reviewer else 'MISSING'}")
    print(f"- apply validation: {apply_validation.valid}")
    if apply_validation.errors:
        print(f"- apply errors (fail-closed): {apply_validation.errors}")
    print("- fixed test allowlist:")
    for c in ALLOWLISTED_TEST_COMMANDS:
        print(f"    - {c}")
    print("- proposed actions:")
    for a in proposal.actions:
        print(f"    - {a.id}: {a.action_type} → {a.target} (risk={a.risk_level})")

    if not apply_validation.valid:
        print("[BLOCKED] proposal is not safely applyable (validation/approval failed closed).",
              file=sys.stderr)
        return 2

    if args.dry_run:
        print("[DRY-RUN] no apply workspace created, no target modified, nothing promoted.",
              file=sys.stderr)
        return 0

    # A real apply requires explicit operator confirmation on top of the marker.
    if not args.approved:
        print("[REJECTED] applying requires explicit --approved (plus the human approval "
              "marker in approval_checklist.md). This phase is workspace-only: it never "
              "modifies stable, a target file, or promotes. Use --dry-run to preview.",
              file=sys.stderr)
        return 3

    test_results = _run_allowlisted_tests() if args.run_tests else {
        "executed": False, "note": "fixed allowlist recorded; not executed (no --run-tests)",
        "commands": list(ALLOWLISTED_TEST_COMMANDS), "results": []}

    out_base = Path(args.output)
    if not out_base.is_absolute():
        out_base = ROOT / args.output
    manifest = apply_proposal(proposal, approval, apply_validation,
                              apply_id=args.apply_id, base_dir=out_base,
                              test_results=test_results)
    print(f"[WROTE] apply workspace: {manifest.workspace_dir} "
          f"(files: {', '.join(manifest.files_written)})", file=sys.stderr)
    print("[WORKSPACE-ONLY] stable untouched; nothing promoted; human review still "
          "required for merge/promotion.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
