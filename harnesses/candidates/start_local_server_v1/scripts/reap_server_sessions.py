"""Manual lease reaper CLI for kept-alive start_local_server sessions.

Scans a session registry dir and/or a runs tree for server_session.json files
and tears down any whose lease has expired (now > started_at + lease_ttl_sec).
Safe to run on a schedule; idempotent and never kills a non-expired server.

Examples:
    python reap_server_sessions.py --sessions-dir runs/_sessions
    python reap_server_sessions.py --runs-dir runs --dry-run
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

_THIS = Path(__file__).resolve()
_SKILL = _THIS.parent / "start_local_server.py"
_spec = importlib.util.spec_from_file_location("start_local_server_reaper", _SKILL)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-dir", default=None, help="flat registry dir of <server_id>.json")
    parser.add_argument("--runs-dir", default=None, help="runs tree to scan for server_session.json")
    parser.add_argument("--now", type=float, default=None, help="override 'now' epoch seconds (testing)")
    parser.add_argument("--dry-run", action="store_true", help="report only; do not kill or delete")
    parser.add_argument("--report", default=None, help="write reaper_report.json to this path")
    args = parser.parse_args()

    if not args.sessions_dir and not args.runs_dir:
        parser.error("provide --sessions-dir and/or --runs-dir")

    report = _mod.reap_sessions(
        sessions_dir=args.sessions_dir,
        runs_dir=args.runs_dir,
        now=args.now,
        dry_run=args.dry_run,
        report_path=args.report,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
