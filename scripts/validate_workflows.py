from __future__ import annotations

import importlib.util
import sys
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

    # Candidate status / promotion / milestone docs (reuse the standalone check).
    doc_errors = _module_errors(root, "validate_candidate_docs")
    if doc_errors:
        print("[FAIL] candidate docs incomplete:")
        for e in doc_errors:
            print(f"  - {e}")
        return 1

    # Phase report pack (reuse the standalone check).
    report_errors = _module_errors(root, "validate_phase_report")
    if report_errors:
        print("[FAIL] phase report incomplete:")
        for e in report_errors:
            print(f"  - {e}")
        return 1

    # Branch B draft pack (reuse the standalone check).
    branch_b_errors = _module_errors(root, "validate_branch_b_draft")
    if branch_b_errors:
        print("[FAIL] Branch B draft pack incomplete:")
        for e in branch_b_errors:
            print(f"  - {e}")
        return 1

    # Secret hygiene (conservative — high-confidence patterns only). Hard-fail on a
    # tracked secret file or a key pattern in a tracked file; also require the
    # gitignore rules. Never prints any secret value.
    sh_errors = _secret_hygiene_errors(root)
    if sh_errors:
        print("[FAIL] secret hygiene:")
        for e in sh_errors:
            print(f"  - {e}")
        return 1

    # Config validation (example + local config if present). No env reads, no API.
    cfg_errors = _module_errors(root, "validate_config")
    if cfg_errors:
        print("[FAIL] config validation:")
        for e in cfg_errors:
            print(f"  - {e}")
        return 1

    # LLM fake smoke (no real API, no env read). Confirms the fake provider works.
    llm_errors = _llm_fake_smoke_errors(root)
    if llm_errors:
        print("[FAIL] llm fake smoke:")
        for e in llm_errors:
            print(f"  - {e}")
        return 1

    print("[PASS] 0-to-1 and 1-to-N workflows are documented")
    print("[PASS] candidate status / promotion / milestone docs are complete")
    print("[PASS] phase report pack is complete")
    print("[PASS] Branch B draft pack is complete (do-not-apply)")
    print("[PASS] secret hygiene OK")
    print("[PASS] config validation OK")
    print("[PASS] llm fake smoke OK")
    return 0


def _llm_fake_smoke_errors(root: Path) -> list[str]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from src.llm import LLMMessage, LLMRequest, build_provider
        provider = build_provider(fake_only=True, root=root)
        resp = provider.complete(LLMRequest(messages=[LLMMessage("user", "fake smoke")]))
        if provider.provider_name != "fake" or resp.provider != "fake" or provider.real_api_enabled:
            return ["llm fake smoke did not use the fake provider"]
        return []
    except Exception as exc:  # noqa: BLE001
        return [f"llm fake smoke failed: {exc}"]


def _secret_hygiene_errors(root: Path) -> list[str]:
    mod_path = root / "scripts" / "check_secret_hygiene.py"
    spec = importlib.util.spec_from_file_location("check_secret_hygiene", mod_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    res = module.check(root)
    errors: list[str] = []
    for f in res["tracked_secret_files"]:
        errors.append(f"secret file is git-tracked: {f}")
    for f, risk in res["key_findings"]:
        errors.append(f"possible key pattern in tracked file {f}: {risk}")
    for r in res["missing_gitignore"]:
        errors.append(f".gitignore missing rule: {r}")
    return errors


def _module_errors(root: Path, script_stem: str) -> list[str]:
    mod_path = root / "scripts" / f"{script_stem}.py"
    spec = importlib.util.spec_from_file_location(script_stem, mod_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check(root)


if __name__ == "__main__":
    raise SystemExit(main())
