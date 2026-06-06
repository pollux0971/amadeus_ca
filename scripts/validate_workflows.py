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

    # Fake planner: required files exist, docs note fake-only/no-execution, and the
    # planner refuses direct-shell skills (no real API, no execution).
    planner_errors = _planner_errors(root)
    if planner_errors:
        print("[FAIL] fake planner:")
        for e in planner_errors:
            print(f"  - {e}")
        return 1

    # Plan execution bridge: required files exist, docs note allowlist / no direct
    # shell / no autonomous replan, the bridge rejects unknown skills, and the
    # plan-only planner category is NOT replaced by planner_execution.
    bridge_errors = _execution_bridge_errors(root)
    if bridge_errors:
        print("[FAIL] plan execution bridge:")
        for e in bridge_errors:
            print(f"  - {e}")
        return 1

    # Phase 2A checkpoint freeze: checkpoint doc + report pack exist, README /
    # quick_resume link the checkpoint, docs state no-autonomous-replan and
    # auto-repair-not-started.
    p2a_errors = _phase_2a_errors(root)
    if p2a_errors:
        print("[FAIL] phase 2A checkpoint:")
        for e in p2a_errors:
            print(f"  - {e}")
        return 1

    # Auto Repair Loop v0: contract + script + eval exist, docs state proposal-only
    # / no apply / human approval / no auto promotion, there is NO repair_apply.py,
    # and the proposal validator rejects stable/safety/promotion targets.
    repair_errors = _repair_errors(root)
    if repair_errors:
        print("[FAIL] repair loop v0:")
        for e in repair_errors:
            print(f"  - {e}")
        return 1

    # Phase 3 checkpoint freeze: checkpoint + report pack exist, README /
    # quick_resume link the checkpoint, docs state proposal-only / no apply /
    # human approval / repair_apply not implemented, and there is NO repair_apply.py.
    p3_errors = _phase_3_errors(root)
    if p3_errors:
        print("[FAIL] phase 3 checkpoint:")
        for e in p3_errors:
            print(f"  - {e}")
        return 1

    print("[PASS] 0-to-1 and 1-to-N workflows are documented")
    print("[PASS] candidate status / promotion / milestone docs are complete")
    print("[PASS] phase report pack is complete")
    print("[PASS] Branch B draft pack is complete (do-not-apply)")
    print("[PASS] secret hygiene OK")
    print("[PASS] config validation OK")
    print("[PASS] llm fake smoke OK")
    print("[PASS] fake planner OK (fake-only, no execution, no direct shell)")
    print("[PASS] plan execution bridge OK (allowlisted, no direct shell, no replan)")
    print("[PASS] phase 2A checkpoint OK (frozen; auto-repair not started)")
    print("[PASS] repair loop v0 OK (proposal-only; no apply; human approval; no promote)")
    print("[PASS] phase 3 checkpoint OK (frozen; repair apply not implemented)")
    return 0


def _phase_3_errors(root: Path) -> list[str]:
    errors: list[str] = []
    checkpoint = "docs/checkpoints/checkpoint-phase-3-repair-proposal-only.md"
    required = [
        checkpoint,
        "reports/phase_3_repair_proposal_only/README.md",
        "reports/phase_3_repair_proposal_only/02_demo_script_repair_proposal.md",
        "reports/phase_3_repair_proposal_only/03_architecture_diagram_repair_proposal.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    # No apply script in v0.
    if (root / "scripts" / "repair_apply.py").exists():
        errors.append("scripts/repair_apply.py exists — Phase 3 must stay proposal-only")

    cp = root / checkpoint
    if cp.exists():
        t = cp.read_text(encoding="utf-8").lower()
        for needle in ("b1ffd56", "proposal-only", "no apply", "repair_apply.py",
                       "no auto promotion", "applied=true", "fake_repair_proposal_only",
                       "--apply", "rejected", "approved patch application"):
            if needle not in t:
                errors.append(f"checkpoint missing phrase: {needle!r}")

    # README + quick_resume must link the Phase 3 checkpoint.
    link = "checkpoint-phase-3-repair-proposal-only"
    for doc in ("README.md", "docs/quick_resume.md"):
        p = root / doc
        if p.exists() and link not in p.read_text(encoding="utf-8"):
            errors.append(f"{doc} missing Phase 3 checkpoint link {link!r}")

    # Docs must state proposal-only / no apply / human approval / no auto promotion
    # / repair_apply not implemented.
    combined = ""
    for doc in ("README.md", "docs/quick_resume.md", "docs/next_milestone_plan.md",
                checkpoint):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for needle in ("proposal-only", "no apply", "human approval", "no auto promotion"):
        if needle not in combined and needle.replace("-", " ") not in combined:
            errors.append(f"phase 3 docs missing phrase: {needle!r}")
    if "repair apply not implemented" not in combined and "repair_apply.py" not in combined:
        errors.append("phase 3 docs missing 'repair apply not implemented'")
    return errors


def _repair_errors(root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        "specs/repair/repair_loop_contract.md",
        "scripts/repair_propose.py",
        "evals/repair/fake_repair_proposal_only.yaml",
        "reports/phase_3_repair_proposal_only/README.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    # There must be NO apply script in v0.
    if (root / "scripts" / "repair_apply.py").exists():
        errors.append("scripts/repair_apply.py exists — v0 must be proposal-only (no apply)")

    # Contract must state the proposal-only guarantees.
    contract = root / "specs/repair/repair_loop_contract.md"
    if contract.exists():
        t = contract.read_text(encoding="utf-8").lower()
        for needle in ("proposal-only", "no apply", "no stable modification",
                       "no auto promotion", "candidate workspace",
                       "human approval", "no direct shell", "no real api"):
            if needle not in t:
                errors.append(f"repair_loop_contract.md missing phrase: {needle!r}")

    # Docs across the set must state proposal-only / no apply / approval / no promote.
    combined = ""
    for doc in ("docs/quick_resume.md", "docs/next_milestone_plan.md",
                "specs/repair/repair_loop_contract.md"):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for needle in ("proposal-only", "no apply", "human approval", "no auto promotion"):
        if needle not in combined and needle.replace("-", " ") not in combined:
            errors.append(f"repair docs missing phrase: {needle!r}")

    # Functional: the proposal validator rejects stable/safety/promotion + shell +
    # applied=true, so no repair code can auto-modify stable.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from src.repair.proposal_validator import validate_proposal
        from src.repair.types import RepairAction, RepairProposal

        def _mk(action_type, target):
            return RepairProposal(id="p", failure_type="test_failed", actions=[
                RepairAction(id="a", action_type=action_type, target=target)])

        bad_cases = [
            ("modify_stable_skill", "harnesses/candidates/c/"),
            ("update_candidate", "skills/inspect_project/"),
            ("update_docs", "src/agents/safety_gate/x.py"),
            ("update_docs", "specs/harness/promotion_policy.md"),
            ("raw_shell", "harnesses/candidates/c/"),
            ("delete_file", "harnesses/candidates/c/"),
        ]
        for at, tgt in bad_cases:
            if validate_proposal(_mk(at, tgt)).valid:
                errors.append(f"proposal validator accepted forbidden ({at} -> {tgt})")
        applied = RepairProposal(id="p", failure_type="x", applied=True, actions=[
            RepairAction(id="a", action_type="noop", target="docs/x.md")])
        if validate_proposal(applied).valid:
            errors.append("proposal validator accepted applied=true")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"repair validator functional check failed: {exc}")
    return errors


def _phase_2a_errors(root: Path) -> list[str]:
    errors: list[str] = []
    checkpoint = "docs/checkpoints/checkpoint-phase-2a-fake-planner-execution.md"
    required = [
        checkpoint,
        "reports/phase_2_fake_planner_execution/README.md",
        "reports/phase_2_fake_planner_execution/02_demo_script_planner_execution.md",
        "reports/phase_2_fake_planner_execution/03_architecture_diagram_planner_execution.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    cp = root / checkpoint
    if cp.exists():
        t = cp.read_text(encoding="utf-8").lower()
        for needle in ("f6e71b0", "no autonomous replan", "allowlisted skills",
                       "no direct shell", "high-risk requires approval",
                       "fake_patch_plan_execution", "fake_full_browser_plan_execution"):
            if needle not in t:
                errors.append(f"checkpoint missing phrase: {needle!r}")

    # README + quick_resume must link the Phase 2A checkpoint.
    link = "checkpoint-phase-2a-fake-planner-execution"
    for doc in ("README.md", "docs/quick_resume.md"):
        p = root / doc
        if p.exists() and link not in p.read_text(encoding="utf-8"):
            errors.append(f"{doc} missing Phase 2A checkpoint link {link!r}")

    # Docs must state no-autonomous-replan and auto-repair-not-started.
    combined = ""
    for doc in ("README.md", "docs/quick_resume.md", "docs/next_milestone_plan.md",
                checkpoint):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    if "no autonomous replan" not in combined:
        errors.append("docs missing 'no autonomous replan'")
    if "auto-repair" not in combined or "not started" not in combined:
        errors.append("docs missing 'auto-repair ... not started'")
    return errors


def _execution_bridge_errors(root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        "specs/planner/plan_execution_bridge_contract.md",
        "scripts/execute_plan.py",
        "evals/planner/fake_patch_plan_execution.yaml",
        "evals/planner/fake_full_browser_plan_execution.yaml",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    contract = root / "specs/planner/plan_execution_bridge_contract.md"
    if contract.exists():
        t = contract.read_text(encoding="utf-8").lower()
        for needle in ("no autonomous replan", "no direct shell", "allowlist"):
            if needle not in t:
                errors.append(f"plan_execution_bridge_contract.md missing phrase: {needle!r}")

    # planner_execution must NOT replace the plan-only planner category.
    plan_only = root / "evals/planner/fake_full_browser_plan.yaml"
    if plan_only.exists():
        if "category: planner\n" not in plan_only.read_text(encoding="utf-8") + "\n":
            errors.append("plan-only planner eval lost its 'category: planner'")
    exec_eval = root / "evals/planner/fake_full_browser_plan_execution.yaml"
    if exec_eval.exists():
        if "category: planner_execution" not in exec_eval.read_text(encoding="utf-8"):
            errors.append("execution eval is not category: planner_execution")

    # Functional: bridge rejects unknown skills + direct shell; refuses unvalidated.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from src.planner.execution_bridge import (
            ALLOWLISTED_SKILLS, FORBIDDEN_SKILLS, build_execution_sequence,
        )
        from src.planner.plan_validator import validate_plan
        from src.planner.types import Plan, PlanStep

        for bad in ("raw_shell", "arbitrary_tool", "some_unknown_tool"):
            p = Plan(goal="g", steps=[PlanStep(id="a", skill=bad)])
            if build_execution_sequence(p, validate_plan(p)).ok:
                errors.append(f"bridge accepted a non-allowlisted skill: {bad}")
        # high risk without approval must fail closed
        hp = Plan(goal="g", steps=[PlanStep(id="a", skill="inspect_project",
                                            risk_level="high", requires_approval=True)])
        if build_execution_sequence(hp, validate_plan(hp), approve_high_risk=False).ok:
            errors.append("bridge executed a high-risk step without approval")
        if not (set(ALLOWLISTED_SKILLS) and set(FORBIDDEN_SKILLS)):
            errors.append("bridge allowlist/denylist is empty")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"bridge functional check failed: {exc}")
    return errors


def _planner_errors(root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        "specs/planner/planner_contract.md",
        "scripts/plan_task.py",
        "evals/planner/fake_full_browser_plan.yaml",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing planner path: {rel}")

    # Docs must state the planner is fake-only and does not execute.
    contract = root / "specs/planner/planner_contract.md"
    if contract.exists():
        text = contract.read_text(encoding="utf-8")
        for needle in ("fake", "never execute"):
            if needle.lower() not in text.lower():
                errors.append(f"planner_contract.md missing phrase: {needle!r}")
    for doc in ("docs/quick_resume.md", "docs/next_milestone_plan.md"):
        p = root / doc
        if p.exists():
            t = p.read_text(encoding="utf-8").lower()
            if "fake-only" not in t and "fake only" not in t:
                errors.append(f"{doc} missing 'fake-only' planner status")
            if "no execution" not in t and "never execute" not in t and "plan-only" not in t:
                errors.append(f"{doc} missing planner 'no execution' note")

    # Functional: the planner refuses direct-shell skills and produces a valid,
    # no-direct-shell plan. No real API call, no execution.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from src.planner.fake_planner import FakePlanner, MARKER_FULL_BROWSER
        from src.planner.plan_validator import FORBIDDEN_SKILLS, validate_plan
        from src.planner.types import Plan, PlannerRequest, PlanStep

        if not FORBIDDEN_SKILLS:
            errors.append("planner FORBIDDEN_SKILLS is empty (direct shell not blocked)")
        bad = Plan(goal="g", steps=[PlanStep(id="x", skill="raw_shell")])
        if validate_plan(bad).valid:
            errors.append("planner validator accepted a direct-shell skill")

        plan = FakePlanner().plan(PlannerRequest(marker=MARKER_FULL_BROWSER)).plan
        res = validate_plan(plan)
        if not res.valid:
            errors.append(f"fake full-browser plan failed validation: {res.errors}")
        if any(str(s).strip().lower() in FORBIDDEN_SKILLS for s in plan.skills):
            errors.append("fake plan contains a direct-shell skill")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"planner functional check failed: {exc}")
    return errors


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
