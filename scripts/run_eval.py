from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()
    print(f"[TODO] run eval task: {args.task}")
    print("This scaffold reserves the interface for future benchmark execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
