"""repair_propose.py — generate a repair PROPOSAL from a failed run (v0).

Auto Repair Loop v0 is PROPOSAL ONLY. This script reads a failed run / failure
report, classifies the failure, generates a deterministic fake repair proposal,
validates it, and writes a redacted proposal workspace. It NEVER applies a patch,
runs a test, modifies a stable skill / safety_gate / promotion_policy, or promotes
anything. There is intentionally NO apply path.

    python scripts/repair_propose.py \
        --failure-report fixtures/repair/fake_failed_eval/summary.md \
        --marker FAKE_REPAIR_TEST_FAILED --dry-run

    python scripts/repair_propose.py --run-dir runs/<failed-run> \
        --marker FAKE_REPAIR_TEST_FAILED \
        --output harnesses/candidates/_repair_proposals
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.repair.failure_analyzer import analyze_failure
from src.repair.fake_repair_planner import FakeRepairPlanner
from src.repair.proposal_validator import validate_proposal
from src.repair.proposal_renderer import render_json, render_markdown
from src.repair.candidate_workspace import create_workspace, DEFAULT_BASE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a repair PROPOSAL (v0; proposal-only, never applies).")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--run-dir", help="A failed run dir (score.json/summary.md/trace.jsonl).")
    src.add_argument("--failure-report", help="A failure report file (summary.md / failure_report.md).")
    parser.add_argument("--marker", default="", help="Repair marker (optional).")
    parser.add_argument("--output", default=str(ROOT / DEFAULT_BASE),
                        help="Base dir for the proposal workspace (default: _repair_proposals).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the redacted proposal; write no workspace.")
    # --apply is intentionally accepted only to REJECT it with a clear message.
    parser.add_argument("--apply", action="store_true",
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.apply:
        print("[REJECTED] --apply is not supported in Auto Repair Loop v0. This phase is "
              "PROPOSAL ONLY: it never applies a patch, modifies a stable skill, or "
              "promotes anything. Apply is a separate, human-approved, not-yet-implemented "
              "step (see specs/repair/repair_loop_contract.md).", file=sys.stderr)
        return 3

    source = args.run_dir or args.failure_report
    src_path = Path(source)
    if not src_path.is_absolute():
        src_path = ROOT / source
    if not src_path.exists():
        print(f"[FAIL] source not found: {source}", file=sys.stderr)
        return 2

    # 1) analyze (redacted, metadata only) -> 2) fake proposal -> 3) validate
    analysis = analyze_failure(src_path)
    proposal = FakeRepairPlanner().propose(analysis, marker=args.marker)
    validation = validate_proposal(proposal)

    # Always print the redacted proposal.
    print(render_markdown(proposal, validation))

    if args.dry_run:
        print("[DRY-RUN] proposal printed; no workspace written, nothing applied.",
              file=sys.stderr)
        return 0 if validation.valid else 1

    out_base = Path(args.output)
    if not out_base.is_absolute():
        out_base = ROOT / args.output
    plan = create_workspace(proposal, analysis, validation, base_dir=out_base)
    print(f"[WROTE] proposal workspace: {plan.workspace_dir} "
          f"(files: {', '.join(plan.files_written)})", file=sys.stderr)
    print("[PROPOSAL-ONLY] nothing applied, executed, or promoted; human approval required.",
          file=sys.stderr)
    return 0 if validation.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
