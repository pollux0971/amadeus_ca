from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_score(run_dir: str) -> dict:
    path = Path(run_dir) / "score.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()

    baseline = load_score(args.baseline)
    candidate = load_score(args.candidate)

    print("# Run Comparison")
    print(f"Baseline success: {baseline.get('task_success')}")
    print(f"Candidate success: {candidate.get('task_success')}")
    print("Promotion decision is not implemented in this scaffold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
