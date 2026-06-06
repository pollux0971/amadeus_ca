"""repair_merge.py — merge an APPROVED apply workspace into a candidate merge workspace.

Candidate Merge v0 is CANDIDATE-WORKSPACE-ONLY. This script reads an apply
workspace, revalidates it, checks the human merge-approval marker + reviewer, and
(only with explicit `--approved` and a non-empty `--reviewer`) merges its proposed
changes into a NEW candidate merge workspace — with a rollback plan and a promotion
review package. It NEVER modifies a real target file, an active candidate, a stable
skill, the safety gate, or the promotion policy, and it NEVER promotes or merges to
stable.

It can run ONLY a fixed, hardcoded allowlist of test commands (never derived from
the apply workspace), and only when explicitly asked with `--run-tests`.

    # safe preview — validate + print the plan, create no workspace
    python scripts/repair_merge.py \
        --apply-workspace fixtures/repair/fake_approved_apply_workspace --dry-run

    # merge into a candidate merge workspace (requires --approved + --reviewer)
    python scripts/repair_merge.py \
        --apply-workspace fixtures/repair/fake_approved_apply_workspace \
        --approved --reviewer "operator" --merge-id fake_merge_smoke
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.repair.merge_validator import validate_merge
from src.repair.candidate_merge import (
    DEFAULT_MERGE_BASE, MERGE_TEST_COMMANDS, create_merge_workspace,
)

_PLACEHOLDER_REVIEWERS = {"", "<name>", "tbd", "todo", "unknown", "none", "n/a"}


def _run_allowlisted_tests() -> dict:
    """Run ONLY the fixed allowlist (never apply-derived). Opt-in via --run-tests."""
    import subprocess  # local import: only used on explicit --run-tests
    results = []
    for cmd in MERGE_TEST_COMMANDS:
        argv = cmd.split()
        if argv and argv[0] == "python":
            argv[0] = sys.executable
        proc = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True)
        results.append({"command": cmd, "ok": proc.returncode == 0, "exit": proc.returncode})
    return {"executed": True, "commands": list(MERGE_TEST_COMMANDS), "results": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge an APPROVED apply workspace into a candidate merge workspace (v0).")
    parser.add_argument("--apply-workspace", required=True,
                        help="Path to an apply workspace (with merge_approval_checklist.md).")
    parser.add_argument("--merge-id", default="repair_merge",
                        help="Identifier for the candidate merge workspace.")
    parser.add_argument("--output", default=str(ROOT / DEFAULT_MERGE_BASE),
                        help="Base dir for the candidate merge workspace.")
    parser.add_argument("--reviewer", default="",
                        help="Named human reviewer (required for a real merge).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate + print the plan; create no merge workspace.")
    parser.add_argument("--approved", action="store_true",
                        help="Explicit operator confirmation required to create the merge workspace.")
    parser.add_argument("--run-tests", action="store_true",
                        help="Also run the FIXED test allowlist (never apply-derived).")
    args = parser.parse_args(argv)

    ws = Path(args.apply_workspace)
    if not ws.is_absolute():
        ws = ROOT / args.apply_workspace
    if not ws.exists():
        print(f"[FAIL] apply workspace not found: {args.apply_workspace}", file=sys.stderr)
        return 2

    validation = validate_merge(ws, reviewer_override=args.reviewer)

    # Always print the plan (redacted).
    print(f"# Repair Merge Plan — apply workspace `{ws.name}`")
    print(f"- merge validation: {validation.valid}")
    print(f"- reviewer: {'set' if validation.reviewer else 'MISSING'}")
    if validation.errors:
        print(f"- merge errors (fail-closed): {validation.errors}")
    print("- fixed test allowlist:")
    for c in MERGE_TEST_COMMANDS:
        print(f"    - {c}")

    if not validation.valid:
        print("[BLOCKED] apply workspace is not safely mergeable (validation/approval failed closed).",
              file=sys.stderr)
        return 2

    if args.dry_run:
        print("[DRY-RUN] no merge workspace created, no target/active-candidate/stable modified, "
              "nothing promoted.", file=sys.stderr)
        return 0

    # A real merge requires explicit operator confirmation on top of the marker.
    if not args.approved:
        print("[REJECTED] merging requires explicit --approved (plus the human merge-approval "
              "marker in merge_approval_checklist.md). This phase is candidate-workspace-only: "
              "it never modifies stable, an active candidate, or promotes. Use --dry-run to preview.",
              file=sys.stderr)
        return 3

    # A real merge requires a non-empty, non-placeholder reviewer.
    if (args.reviewer or "").strip().lower() in _PLACEHOLDER_REVIEWERS:
        print("[REJECTED] merging requires a non-empty --reviewer (a named human).",
              file=sys.stderr)
        return 3

    test_results = _run_allowlisted_tests() if args.run_tests else {
        "executed": False, "note": "fixed allowlist recorded; not executed (no --run-tests)",
        "commands": list(MERGE_TEST_COMMANDS), "results": []}

    out_base = Path(args.output)
    if not out_base.is_absolute():
        out_base = ROOT / args.output
    manifest = create_merge_workspace(ws, validation, merge_id=args.merge_id,
                                      base_dir=out_base, reviewer=args.reviewer.strip(),
                                      test_results=test_results)
    print(f"[WROTE] candidate merge workspace: {manifest.workspace_dir} "
          f"(files: {', '.join(manifest.files_written)})", file=sys.stderr)
    print("[CANDIDATE-WORKSPACE-ONLY] stable untouched; active candidate untouched; nothing "
          "promoted; rollback plan + promotion review package included; human review required "
          "before staging/stable.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
