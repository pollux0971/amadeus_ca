from __future__ import annotations

from pathlib import Path

REQUIRED_WORKFLOW_PATHS = [
    "START_HERE.md",
    "WORKFLOW_INDEX.md",
    "docs/14_zero_to_one_workflow.md",
    "docs/15_one_to_n_workflow.md",
    "specs/workflows/zero_to_one_contract.md",
    "specs/workflows/one_to_n_contract.md",
    "templates/feature_intake/feature_intake_template.yaml",
    "templates/eval_task/eval_task_template.yaml",
    "templates/extension_adapter/adapter_template.md",
    "templates/skill_package/SKILL_TEMPLATE.md",
]

REQUIRED_ZERO_TO_ONE_KEYWORDS = [
    "walking skeleton",
    "thin vertical slice",
    "Skill Package Runner",
    "Trace Logger",
    "CLI Agent",
    "Browser Agent",
    "Verifier",
    "vite_login_bug",
    "0→1 完成檢查清單",
]

REQUIRED_ONE_TO_N_KEYWORDS = [
    "Feature Intake",
    "External Source Manifest",
    "Brownfield Inspection",
    "Adapter Design",
    "Contract Tests",
    "Minimal Eval Task",
    "Promotion",
    "rollback",
    "1→N 完成檢查清單",
]


def require_keywords(path: Path, keywords: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [keyword for keyword in keywords if keyword not in text]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing_paths = [p for p in REQUIRED_WORKFLOW_PATHS if not (root / p).exists()]
    if missing_paths:
        print("[FAIL] missing workflow paths:")
        for p in missing_paths:
            print(f"  - {p}")
        return 1

    missing_zero = require_keywords(root / "docs/14_zero_to_one_workflow.md", REQUIRED_ZERO_TO_ONE_KEYWORDS)
    missing_n = require_keywords(root / "docs/15_one_to_n_workflow.md", REQUIRED_ONE_TO_N_KEYWORDS)

    if missing_zero or missing_n:
        print("[FAIL] workflow docs are incomplete")
        if missing_zero:
            print("  zero-to-one missing keywords:")
            for k in missing_zero:
                print(f"    - {k}")
        if missing_n:
            print("  one-to-n missing keywords:")
            for k in missing_n:
                print(f"    - {k}")
        return 1

    print("[PASS] 0-to-1 and 1-to-N workflows are documented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
