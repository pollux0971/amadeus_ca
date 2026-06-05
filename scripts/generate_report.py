from __future__ import annotations

from pathlib import Path
import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run)
    score_path = run_dir / "score.json"
    trace_path = run_dir / "trace.jsonl"

    report = ["# Generated Report", ""]
    if score_path.exists():
        score = json.loads(score_path.read_text(encoding="utf-8"))
        report.append(f"- task_id: {score.get('task_id')}")
        report.append(f"- success: {score.get('task_success')}")
        report.append(f"- score: {score.get('score')}")
    if trace_path.exists():
        steps = trace_path.read_text(encoding="utf-8").strip().splitlines()
        report.append(f"- trace_steps: {len([s for s in steps if s.strip()])}")

    (run_dir / "generated_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"[PASS] wrote {run_dir / 'generated_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
