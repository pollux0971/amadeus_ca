"""staging_promote.py — promote an APPROVED candidate merge workspace into a staging workspace.

Staging Promotion v0 is STAGING-WORKSPACE-ONLY. This script reads a candidate merge
workspace, revalidates it, checks the human staging-approval marker + reviewer,
verifies the rollback plan, and (only with explicit `--approved` and a non-empty
`--reviewer`) promotes its merged changes into a NEW staging workspace — with
regression results and a stable-promotion checklist. It NEVER modifies a real
target file, an active candidate, a stable skill, the safety gate, or the promotion
policy, and it NEVER stable-promotes.

It can run ONLY a fixed, hardcoded allowlist of test commands (never derived from
the merge workspace), and only when explicitly asked with `--run-tests`.

    # safe preview — validate + print the plan, create no workspace
    python scripts/staging_promote.py \
        --merge-workspace fixtures/repair/fake_approved_merge_workspace --dry-run

    # promote into a staging workspace (requires --approved + --reviewer)
    python scripts/staging_promote.py \
        --merge-workspace fixtures/repair/fake_approved_merge_workspace \
        --approved --reviewer "operator" --staging-id fake_staging_smoke
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.repair.staging_validator import validate_staging
from src.repair.staging_promotion import (
    DEFAULT_STAGING_BASE, STAGING_TEST_COMMANDS, create_staging_workspace,
)

_PLACEHOLDER_REVIEWERS = {"", "<name>", "tbd", "todo", "unknown", "none", "n/a"}


def _run_allowlisted_tests() -> dict:
    """Run ONLY the fixed allowlist (never merge-derived). Opt-in via --run-tests."""
    import subprocess  # local import: only used on explicit --run-tests
    results = []
    for cmd in STAGING_TEST_COMMANDS:
        argv = cmd.split()
        if argv and argv[0] == "python":
            argv[0] = sys.executable
        proc = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True)
        results.append({"command": cmd, "ok": proc.returncode == 0, "exit": proc.returncode})
    return {"executed": True, "commands": list(STAGING_TEST_COMMANDS), "results": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Promote an APPROVED candidate merge workspace into a staging workspace (v0).")
    parser.add_argument("--merge-workspace", required=True,
                        help="Path to a candidate merge workspace (with staging_approval_checklist.md).")
    parser.add_argument("--staging-id", default="staging_promote",
                        help="Identifier for the staging promotion workspace.")
    parser.add_argument("--output", default=str(ROOT / DEFAULT_STAGING_BASE),
                        help="Base dir for the staging promotion workspace.")
    parser.add_argument("--reviewer", default="",
                        help="Named human reviewer (required for a real staging promotion).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate + print the plan; create no staging workspace.")
    parser.add_argument("--approved", action="store_true",
                        help="Explicit operator confirmation required to create the staging workspace.")
    parser.add_argument("--run-tests", action="store_true",
                        help="Also run the FIXED test allowlist (never merge-derived).")
    args = parser.parse_args(argv)

    ws = Path(args.merge_workspace)
    if not ws.is_absolute():
        ws = ROOT / args.merge_workspace
    if not ws.exists():
        print(f"[FAIL] merge workspace not found: {args.merge_workspace}", file=sys.stderr)
        return 2

    validation = validate_staging(ws, reviewer_override=args.reviewer)

    # Always print the plan (redacted).
    print(f"# Staging Promotion Plan — merge workspace `{ws.name}`")
    print(f"- staging validation: {validation.valid}")
    print(f"- reviewer: {'set' if validation.reviewer else 'MISSING'}")
    print(f"- rollback plan present: {validation.rollback_present}")
    if validation.errors:
        print(f"- staging errors (fail-closed): {validation.errors}")
    print("- fixed test allowlist:")
    for c in STAGING_TEST_COMMANDS:
        print(f"    - {c}")

    if not validation.valid:
        print("[BLOCKED] merge workspace is not safely stageable (validation/approval failed closed).",
              file=sys.stderr)
        return 2

    if args.dry_run:
        print("[DRY-RUN] no staging workspace created, no target/active-candidate/stable modified, "
              "nothing stable-promoted.", file=sys.stderr)
        return 0

    # A real staging promotion requires explicit operator confirmation on top of the marker.
    if not args.approved:
        print("[REJECTED] staging promotion requires explicit --approved (plus the human "
              "staging-approval marker in staging_approval_checklist.md). This phase is "
              "staging-workspace-only: it never modifies stable, an active candidate, or "
              "stable-promotes. Use --dry-run to preview.", file=sys.stderr)
        return 3

    # A real staging promotion requires a non-empty, non-placeholder reviewer.
    if (args.reviewer or "").strip().lower() in _PLACEHOLDER_REVIEWERS:
        print("[REJECTED] staging promotion requires a non-empty --reviewer (a named human).",
              file=sys.stderr)
        return 3

    regression_results = _run_allowlisted_tests() if args.run_tests else {
        "executed": False, "note": "fixed allowlist recorded; not executed (no --run-tests)",
        "commands": list(STAGING_TEST_COMMANDS), "results": []}

    out_base = Path(args.output)
    if not out_base.is_absolute():
        out_base = ROOT / args.output
    manifest = create_staging_workspace(ws, validation, staging_id=args.staging_id,
                                        base_dir=out_base, reviewer=args.reviewer.strip(),
                                        regression_results=regression_results)
    print(f"[WROTE] staging promotion workspace: {manifest.workspace_dir} "
          f"(files: {', '.join(manifest.files_written)})", file=sys.stderr)
    print("[STAGING-WORKSPACE-ONLY] stable untouched; active candidate untouched; nothing "
          "stable-promoted; rollback verification + stable promotion checklist included; "
          "human review + promotion policy still required before stable.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
