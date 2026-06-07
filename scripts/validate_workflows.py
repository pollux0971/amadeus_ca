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

    # Epic / Story backlog (reuse the standalone check).
    epics_errors = _module_errors(root, "validate_epics")
    if epics_errors:
        print("[FAIL] epics backlog incomplete:")
        for e in epics_errors:
            print(f"  - {e}")
        return 1

    # Multimodal / data channels planning docs (reuse the standalone check).
    mm_errors = _module_errors(root, "validate_multimodal_planning")
    if mm_errors:
        print("[FAIL] multimodal planning docs incomplete:")
        for e in mm_errors:
            print(f"  - {e}")
        return 1

    # Read-only UI dashboard skeleton (reuse the standalone check).
    dash_errors = _module_errors(root, "validate_dashboard")
    if dash_errors:
        print("[FAIL] dashboard skeleton incomplete:")
        for e in dash_errors:
            print(f"  - {e}")
        return 1

    # Project demo package (reuse the standalone check).
    demo_errors = _module_errors(root, "validate_demo_package")
    if demo_errors:
        print("[FAIL] demo package incomplete:")
        for e in demo_errors:
            print(f"  - {e}")
        return 1

    # Stable promotion readiness audit (reuse the standalone check).
    audit_errors = _module_errors(root, "validate_stable_promotion_audit")
    if audit_errors:
        print("[FAIL] stable promotion audit incomplete:")
        for e in audit_errors:
            print(f"  - {e}")
        return 1

    # Project report (reuse the standalone check).
    report_doc_errors = _module_errors(root, "validate_project_report")
    if report_doc_errors:
        print("[FAIL] project report incomplete:")
        for e in report_doc_errors:
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

    # Real provider safety (fake default, fail-closed, env-var-name only, redacted).
    rp_errors = _real_provider_safety_errors(root)
    if rp_errors:
        print("[FAIL] real provider safety:")
        for e in rp_errors:
            print(f"  - {e}")
        return 1

    # Real provider live smoke (OpenAI only this round): script exists, dry-run is
    # the default, --real-call is gated, the prompt is FIXED (no arbitrary prompt),
    # output is redacted, and it fails closed without the env var. No real API call
    # is made by this check.
    ls_errors = _real_provider_live_smoke_errors(root)
    if ls_errors:
        print("[FAIL] real provider live smoke:")
        for e in ls_errors:
            print(f"  - {e}")
        return 1

    # Test environment baseline: the baseline doc + checker exist and agree on the
    # known environment-gap tests; the checker reports (never fails) on a missing
    # `python`/.venv/Playwright. This is SOFT — env gaps print as warnings and do NOT
    # fail the gate (a missing `python` on PATH is never a failure).
    teb_errors = _test_environment_baseline_errors(root)
    if teb_errors:
        print("[FAIL] test environment baseline:")
        for e in teb_errors:
            print(f"  - {e}")
        return 1

    # OpenAI planner live plan-only (OpenAI Planner Live Plan-Only v0): script + eval
    # + tests exist; dry-run default makes no API call; --real-call is gated; the
    # planner is plan-only and never auto-repairs; output is redacted. No real API
    # call is made by this check (dry-run only).
    lp_errors = _openai_planner_live_plan_errors(root)
    if lp_errors:
        print("[FAIL] openai planner live plan:")
        for e in lp_errors:
            print(f"  - {e}")
        return 1

    # OpenAI plan review package (review-only): generator + tests + committed example
    # exist; the package marks NOT APPROVED / NOT EXECUTED; a non-low-risk or
    # non-allowlisted plan is BLOCKED; nothing is executed. No real API call here.
    pr_errors = _openai_plan_review_errors(root)
    if pr_errors:
        print("[FAIL] openai plan review package:")
        for e in pr_errors:
            print(f"  - {e}")
        return 1

    # OpenAI read-only plan execution gate: gate module + script + eval + tests exist;
    # dry-run executes nothing; a real run needs --approved + checklist marker +
    # reviewer + a valid allowlisted plan; only inspect_project is allowlisted; all
    # other skills are refused; no shell / repair / promotion. No real API call here.
    rx_errors = _openai_readonly_execution_errors(root)
    if rx_errors:
        print("[FAIL] openai read-only plan execution gate:")
        for e in rx_errors:
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

    # Provider-aware planner (dry-run): fake default, real fail-closed without
    # opt-in, real provider HELD but never called, plan-only, redacted. No real API.
    pp_errors = _planner_provider_integration_errors(root)
    if pp_errors:
        print("[FAIL] planner provider integration:")
        for e in pp_errors:
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
    # human approval.
    p3_errors = _phase_3_errors(root)
    if p3_errors:
        print("[FAIL] phase 3 checkpoint:")
        for e in p3_errors:
            print(f"  - {e}")
        return 1

    # Approved Patch Application v0: contract + script + eval exist, docs state
    # human-approved-only / workspace-only / no stable modification / no auto
    # promotion / fixed test allowlist; repair_apply.py uses no raw shell and
    # modifies no stable file.
    apply_errors = _approved_apply_errors(root)
    if apply_errors:
        print("[FAIL] approved patch application:")
        for e in apply_errors:
            print(f"  - {e}")
        return 1

    # Phase 4 checkpoint freeze: checkpoint + report pack exist, README /
    # quick_resume link the checkpoint, docs state workspace-only / human-approved /
    # no stable mod / no auto promotion / merge + promotion not started.
    p4_errors = _phase_4_errors(root)
    if p4_errors:
        print("[FAIL] phase 4 checkpoint:")
        for e in p4_errors:
            print(f"  - {e}")
        return 1

    # Candidate Merge v0: contract + script + eval + report exist, docs state
    # human-reviewed-only / candidate-workspace-only / no stable mod / no auto
    # promotion / rollback required / promotion review package required / fixed test
    # allowlist; repair_merge.py uses no raw shell and modifies no stable file.
    merge_errors = _candidate_merge_errors(root)
    if merge_errors:
        print("[FAIL] candidate merge:")
        for e in merge_errors:
            print(f"  - {e}")
        return 1

    # Phase 5 checkpoint freeze: checkpoint + report pack exist, README /
    # quick_resume link the checkpoint, docs state candidate-workspace-only /
    # human-reviewed / no active-candidate + stable mod / rollback + promotion review
    # package / staging + stable promotion not started.
    p5_errors = _phase_5_errors(root)
    if p5_errors:
        print("[FAIL] phase 5 checkpoint:")
        for e in p5_errors:
            print(f"  - {e}")
        return 1

    # Staging Promotion v0: contract + script + eval + report exist, docs state
    # human-reviewed-only / staging-workspace-only / no stable mod / no stable
    # promotion / rollback verification + regression required / fixed test allowlist;
    # staging_promote.py uses no raw shell and modifies no stable file.
    staging_errors = _staging_promotion_errors(root)
    if staging_errors:
        print("[FAIL] staging promotion:")
        for e in staging_errors:
            print(f"  - {e}")
        return 1

    # Phase 6 checkpoint freeze: checkpoint + report pack exist, README /
    # quick_resume link the checkpoint, docs state staging-workspace-only /
    # human-reviewed / no active-candidate + stable mod / rollback verification +
    # stable promotion checklist / stable promotion not started.
    p6_errors = _phase_6_errors(root)
    if p6_errors:
        print("[FAIL] phase 6 checkpoint:")
        for e in p6_errors:
            print(f"  - {e}")
        return 1

    print("[PASS] 0-to-1 and 1-to-N workflows are documented")
    print("[PASS] candidate status / promotion / milestone docs are complete")
    print("[PASS] phase report pack is complete")
    print("[PASS] Branch B draft pack is complete (do-not-apply)")
    print("[PASS] epics backlog is complete (one bounded story; boundaries documented)")
    print("[PASS] multimodal planning docs complete (planning only; isolation documented)")
    print("[PASS] dashboard skeleton OK (read-only; no action execution; no secret)")
    print("[PASS] demo package OK (safe demo commands; boundaries documented)")
    print("[PASS] stable promotion audit OK (recommendation: NO-GO/BLOCKED; not promoted)")
    print("[PASS] project report OK (diagram + timeline + results + safety + script)")
    print("[PASS] secret hygiene OK")
    print("[PASS] config validation OK")
    print("[PASS] llm fake smoke OK")
    print("[PASS] real provider safety OK (fake default; fail-closed; env-var-name only; redacted)")
    print("[PASS] real provider live smoke OK (OpenAI only; dry-run default; --real-call gated; fixed prompt; redacted; fail-closed)")
    print("[PASS] test environment baseline OK (documented; checker present; python-not-on-PATH is warning-only)")
    print("[PASS] openai planner live plan OK (plan-only; dry-run default; --real-call gated; validated-or-blocked; no auto-repair; redacted)")
    print("[PASS] openai plan review package OK (review-only; NOT APPROVED/NOT EXECUTED; low-risk allowlisted or BLOCKED; redacted)")
    print("[PASS] openai read-only plan execution gate OK (human-approved; inspect_project-only; dry-run default; no shell/repair/promotion; redacted)")
    print("[PASS] fake planner OK (fake-only, no execution, no direct shell)")
    print("[PASS] planner provider integration OK (fake default; fail-closed; real held, not called; plan-only)")
    print("[PASS] plan execution bridge OK (allowlisted, no direct shell, no replan)")
    print("[PASS] phase 2A checkpoint OK (frozen; auto-repair not started)")
    print("[PASS] repair loop v0 OK (proposal-only; no apply; human approval; no promote)")
    print("[PASS] phase 3 checkpoint OK (frozen)")
    print("[PASS] approved patch application OK (human-approved; workspace-only; no promote)")
    print("[PASS] phase 4 checkpoint OK (frozen; merge/promotion not started)")
    print("[PASS] candidate merge OK (human-reviewed; candidate-workspace-only; no promote)")
    print("[PASS] phase 5 checkpoint OK (frozen; staging/stable promotion not started)")
    print("[PASS] staging promotion OK (human-reviewed; staging-workspace-only; no stable promote)")
    print("[PASS] phase 6 checkpoint OK (frozen; stable promotion not started)")
    return 0


def _phase_6_errors(root: Path) -> list[str]:
    errors: list[str] = []
    checkpoint = "docs/checkpoints/checkpoint-phase-6-staging-promotion.md"
    required = [
        checkpoint,
        "reports/phase_6_staging_promotion/README.md",
        "reports/phase_6_staging_promotion/02_demo_script_staging_promotion.md",
        "reports/phase_6_staging_promotion/03_architecture_diagram_staging_promotion.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    if not (root / "scripts" / "staging_promote.py").exists():
        errors.append("scripts/staging_promote.py is missing")

    cp = root / checkpoint
    if cp.exists():
        t = cp.read_text(encoding="utf-8").lower()
        for needle in ("78ecae3", "staging-workspace-only", "human-reviewed only",
                       "no active candidate modification", "no stable modification",
                       "no auto promotion", "no stable promotion", "staged_changes",
                       "rollback_verification.md", "stable_promotion_checklist.md",
                       "fixed test command allowlist", "fake_staging_promotion",
                       "staging_promote.py"):
            if needle not in t:
                errors.append(f"checkpoint missing phrase: {needle!r}")

    link = "checkpoint-phase-6-staging-promotion"
    for doc in ("README.md", "docs/quick_resume.md"):
        p = root / doc
        if p.exists() and link not in p.read_text(encoding="utf-8"):
            errors.append(f"{doc} missing Phase 6 checkpoint link {link!r}")

    combined = ""
    for doc in ("README.md", "docs/quick_resume.md", "docs/next_milestone_plan.md",
                checkpoint):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for needle in ("staging-workspace-only", "human-reviewed", "no active candidate",
                   "no stable", "no stable promotion", "rollback verification",
                   "stable promotion checklist", "fixed test command allowlist"):
        if needle not in combined and needle.replace("-", " ") not in combined:
            errors.append(f"phase 6 docs missing phrase: {needle!r}")
    if "stable promotion not started" not in combined:
        errors.append("phase 6 docs missing 'stable promotion not started'")

    for bad in ("stable promotion completed", "stable promotion is complete",
                "stable promotion done"):
        if bad in combined:
            errors.append(f"docs falsely claim {bad!r}")
    return errors


def _staging_promotion_errors(root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        "specs/repair/staging_promotion_contract.md",
        "scripts/staging_promote.py",
        "evals/repair/fake_staging_promotion.yaml",
        "reports/phase_6_staging_promotion/README.md",
        "fixtures/repair/fake_approved_merge_workspace/staging_approval_checklist.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    # Contract must state the staging guarantees.
    contract = root / "specs/repair/staging_promotion_contract.md"
    if contract.exists():
        t = contract.read_text(encoding="utf-8").lower()
        for needle in ("human-reviewed only", "staging workspace only",
                       "no stable modification", "no stable promotion", "no auto promotion",
                       "rollback verification required", "regression required",
                       "promotion policy still required", "fixed test command allowlist",
                       "no raw shell"):
            if needle not in t:
                errors.append(f"staging_promotion_contract.md missing phrase: {needle!r}")

    # staging_promote.py must not use a raw shell and must require approval + reviewer.
    sp = root / "scripts" / "staging_promote.py"
    if sp.exists():
        src = sp.read_text(encoding="utf-8")
        if "shell=True" in src:
            errors.append("staging_promote.py uses shell=True (raw shell forbidden)")
        if "os.system" in src:
            errors.append("staging_promote.py uses os.system (raw shell forbidden)")
        if "--approved" not in src:
            errors.append("staging_promote.py does not require --approved")
        if "--reviewer" not in src:
            errors.append("staging_promote.py does not require --reviewer")

    # Docs must state the staging guarantees.
    combined = ""
    for doc in ("docs/quick_resume.md", "docs/next_milestone_plan.md",
                "specs/repair/staging_promotion_contract.md",
                "reports/phase_6_staging_promotion/README.md"):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for needle in ("staging workspace only", "no stable", "no stable promotion",
                   "no auto promotion", "rollback verification", "regression",
                   "human-reviewed", "fixed test command allowlist"):
        if needle not in combined and needle.replace("-", " ") not in combined:
            errors.append(f"staging docs missing phrase: {needle!r}")
    for bad in ("stable promotion completed", "stable promotion is complete",
                "stable promotion done"):
        if bad in combined:
            errors.append(f"docs falsely claim {bad!r}")

    # Functional: the staging validator rejects missing-approval / stable-target /
    # promoted-merge so no staging code can touch stable.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        import json as _json
        import shutil as _shutil
        import tempfile as _tempfile
        from src.repair.staging_validator import validate_staging

        fixture = root / "fixtures" / "repair" / "fake_approved_merge_workspace"
        if fixture.exists():
            if not validate_staging(fixture).valid:
                errors.append("staging validator rejected the valid approved fixture")
            tmp = _tempfile.mkdtemp()
            try:
                ws = Path(tmp) / "mw"
                _shutil.copytree(fixture, ws)
                (ws / "staging_approval_checklist.md").write_text("no marker", encoding="utf-8")
                if validate_staging(ws).valid:
                    errors.append("staging validator accepted a missing approval marker")
                _shutil.copyfile(fixture / "staging_approval_checklist.md",
                                 ws / "staging_approval_checklist.md")
                mf = ws / "merge_manifest.json"
                data = _json.loads(mf.read_text(encoding="utf-8"))
                data["stable_modified"] = True
                mf.write_text(_json.dumps(data), encoding="utf-8")
                if validate_staging(ws).valid:
                    errors.append("staging validator accepted a stable_modified merge manifest")
            finally:
                _shutil.rmtree(tmp, ignore_errors=True)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"staging functional check failed: {exc}")
    return errors


def _phase_5_errors(root: Path) -> list[str]:
    errors: list[str] = []
    checkpoint = "docs/checkpoints/checkpoint-phase-5-candidate-merge.md"
    required = [
        checkpoint,
        "reports/phase_5_candidate_merge/README.md",
        "reports/phase_5_candidate_merge/02_demo_script_candidate_merge.md",
        "reports/phase_5_candidate_merge/03_architecture_diagram_candidate_merge.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    if not (root / "scripts" / "repair_merge.py").exists():
        errors.append("scripts/repair_merge.py is missing")

    cp = root / checkpoint
    if cp.exists():
        t = cp.read_text(encoding="utf-8").lower()
        for needle in ("b5ee165", "candidate-workspace-only", "human-reviewed only",
                       "no active candidate modification", "no stable modification",
                       "no auto promotion", "no staging promotion", "no stable promotion",
                       "rollback_plan.md", "promotion_review_package.md",
                       "fixed test command allowlist", "fake_candidate_merge",
                       "repair_merge.py"):
            if needle not in t:
                errors.append(f"checkpoint missing phrase: {needle!r}")

    link = "checkpoint-phase-5-candidate-merge"
    for doc in ("README.md", "docs/quick_resume.md"):
        p = root / doc
        if p.exists() and link not in p.read_text(encoding="utf-8"):
            errors.append(f"{doc} missing Phase 5 checkpoint link {link!r}")

    combined = ""
    for doc in ("README.md", "docs/quick_resume.md", "docs/next_milestone_plan.md",
                checkpoint):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for needle in ("candidate-workspace-only", "human-reviewed", "no active candidate",
                   "no stable", "no auto promotion", "rollback plan",
                   "promotion review package", "fixed test command allowlist"):
        if needle not in combined and needle.replace("-", " ") not in combined:
            errors.append(f"phase 5 docs missing phrase: {needle!r}")
    # Stable promotion is still not started after Phase 6 (staging may ship; the
    # "staging promotion not started" wording is living and the frozen Phase 5
    # checkpoint doc above keeps that historical record).
    if "stable promotion not started" not in combined:
        errors.append("phase 5 docs missing 'stable promotion not started'")

    for bad in ("staging promotion completed", "staging promotion is complete",
                "stable promotion completed", "stable promotion is complete",
                "stable promotion done"):
        if bad in combined:
            errors.append(f"docs falsely claim {bad!r}")
    return errors


def _candidate_merge_errors(root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        "specs/repair/candidate_merge_contract.md",
        "scripts/repair_merge.py",
        "evals/repair/fake_candidate_merge.yaml",
        "reports/phase_5_candidate_merge/README.md",
        "fixtures/repair/fake_approved_apply_workspace/merge_approval_checklist.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    # Contract must state the merge guarantees.
    contract = root / "specs/repair/candidate_merge_contract.md"
    if contract.exists():
        t = contract.read_text(encoding="utf-8").lower()
        for needle in ("human-reviewed only", "candidate workspace only",
                       "no stable modification", "no auto promotion", "rollback required",
                       "promotion review package required", "fixed test command allowlist",
                       "no raw shell"):
            if needle not in t:
                errors.append(f"candidate_merge_contract.md missing phrase: {needle!r}")

    # repair_merge.py must not use a raw shell and must require approval + reviewer.
    rm = root / "scripts" / "repair_merge.py"
    if rm.exists():
        src = rm.read_text(encoding="utf-8")
        if "shell=True" in src:
            errors.append("repair_merge.py uses shell=True (raw shell forbidden)")
        if "os.system" in src:
            errors.append("repair_merge.py uses os.system (raw shell forbidden)")
        if "--approved" not in src:
            errors.append("repair_merge.py does not require --approved")
        if "--reviewer" not in src:
            errors.append("repair_merge.py does not require --reviewer")

    # Docs must state the merge guarantees.
    combined = ""
    for doc in ("docs/quick_resume.md", "docs/next_milestone_plan.md",
                "specs/repair/candidate_merge_contract.md",
                "reports/phase_5_candidate_merge/README.md"):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for needle in ("candidate workspace only", "no stable", "no auto promotion",
                   "rollback", "promotion review package", "human-reviewed",
                   "fixed test command allowlist"):
        if needle not in combined and needle.replace("-", " ") not in combined:
            errors.append(f"merge docs missing phrase: {needle!r}")
    for bad in ("stable promotion completed", "stable promotion is complete",
                "stable promotion done"):
        if bad in combined:
            errors.append(f"docs falsely claim {bad!r}")

    # Functional: the merge validator rejects missing-approval / stable-target /
    # promoted apply so no merge code can touch stable.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        import json as _json
        import shutil as _shutil
        import tempfile as _tempfile
        from src.repair.merge_validator import validate_merge

        fixture = root / "fixtures" / "repair" / "fake_approved_apply_workspace"
        if fixture.exists():
            if not validate_merge(fixture).valid:
                errors.append("merge validator rejected the valid approved fixture")
            tmp = _tempfile.mkdtemp()
            try:
                ws = Path(tmp) / "aw"
                _shutil.copytree(fixture, ws)
                (ws / "merge_approval_checklist.md").write_text("no marker", encoding="utf-8")
                if validate_merge(ws).valid:
                    errors.append("merge validator accepted a missing approval marker")
                # restore approval, break the workspace-only invariant
                _shutil.copyfile(fixture / "merge_approval_checklist.md",
                                 ws / "merge_approval_checklist.md")
                mf = ws / "apply_manifest.json"
                data = _json.loads(mf.read_text(encoding="utf-8"))
                data["promoted"] = True
                mf.write_text(_json.dumps(data), encoding="utf-8")
                if validate_merge(ws).valid:
                    errors.append("merge validator accepted a promoted apply manifest")
            finally:
                _shutil.rmtree(tmp, ignore_errors=True)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"candidate-merge functional check failed: {exc}")
    return errors


def _phase_4_errors(root: Path) -> list[str]:
    errors: list[str] = []
    checkpoint = "docs/checkpoints/checkpoint-phase-4-approved-patch-application.md"
    required = [
        checkpoint,
        "reports/phase_4_approved_patch_application/README.md",
        "reports/phase_4_approved_patch_application/02_demo_script_approved_apply.md",
        "reports/phase_4_approved_patch_application/03_architecture_diagram_approved_apply.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    # repair_apply.py must still exist and stay workspace-only.
    if not (root / "scripts" / "repair_apply.py").exists():
        errors.append("scripts/repair_apply.py is missing")

    cp = root / checkpoint
    if cp.exists():
        t = cp.read_text(encoding="utf-8").lower()
        for needle in ("0eca9de", "workspace-only", "human-approved only",
                       "no stable modification", "no auto promotion", "no merge",
                       "fixed test command allowlist", "fake_approved_patch_application",
                       "repair_apply.py", "merge + promotion"):
            if needle not in t:
                errors.append(f"checkpoint missing phrase: {needle!r}")

    # README + quick_resume must link the Phase 4 checkpoint.
    link = "checkpoint-phase-4-approved-patch-application"
    for doc in ("README.md", "docs/quick_resume.md"):
        p = root / doc
        if p.exists() and link not in p.read_text(encoding="utf-8"):
            errors.append(f"{doc} missing Phase 4 checkpoint link {link!r}")

    # Docs must state workspace-only / human-approved / no stable mod / no auto
    # promotion / fixed test allowlist. (The "merge not started" wording is living
    # and advances once Candidate Merge ships; the frozen Phase 4 checkpoint doc
    # above keeps that historical record.)
    combined = ""
    for doc in ("README.md", "docs/quick_resume.md", "docs/next_milestone_plan.md",
                checkpoint):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for needle in ("workspace-only", "human-approved", "no stable",
                   "no auto promotion", "fixed test command allowlist"):
        if needle not in combined and needle.replace("-", " ") not in combined:
            errors.append(f"phase 4 docs missing phrase: {needle!r}")
    # Promotion is still not started after Phase 5 (merge done, promotion not).
    if "promotion not started" not in combined and "promotion is not started" not in combined:
        errors.append("phase 4 docs missing 'promotion not started'")

    # Docs must NOT claim stable promotion is completed/done.
    for bad in ("stable promotion completed", "stable promotion is complete",
                "stable promotion done"):
        if bad in combined:
            errors.append(f"docs falsely claim {bad!r}")
    return errors


def _approved_apply_errors(root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        "specs/repair/approved_patch_application_contract.md",
        "scripts/repair_apply.py",
        "evals/repair/fake_approved_patch_application.yaml",
        "reports/phase_4_approved_patch_application/README.md",
        "fixtures/repair/fake_approved_proposal_workspace/approval_checklist.md",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    # Contract must state the apply guarantees.
    contract = root / "specs/repair/approved_patch_application_contract.md"
    if contract.exists():
        t = contract.read_text(encoding="utf-8").lower()
        for needle in ("human-approved only", "workspace only", "no stable modification",
                       "no auto promotion", "fixed test command allowlist",
                       "no raw shell"):
            if needle not in t:
                errors.append(f"approved_patch_application_contract.md missing phrase: {needle!r}")

    # repair_apply.py must not use a raw shell and must not write to stable.
    rap = root / "scripts" / "repair_apply.py"
    if rap.exists():
        src = rap.read_text(encoding="utf-8")
        if "shell=True" in src:
            errors.append("repair_apply.py uses shell=True (raw shell forbidden)")
        if "os.system" in src:
            errors.append("repair_apply.py uses os.system (raw shell forbidden)")
        # it must require explicit approval before applying
        if "--approved" not in src:
            errors.append("repair_apply.py does not require --approved")

    # Docs must state human-approved / workspace-only / no stable mod / no auto
    # promotion / fixed test allowlist.
    combined = ""
    for doc in ("docs/quick_resume.md", "docs/next_milestone_plan.md",
                "specs/repair/approved_patch_application_contract.md",
                "reports/phase_4_approved_patch_application/README.md"):
        p = root / doc
        if p.exists():
            combined += p.read_text(encoding="utf-8").lower() + "\n"
    for needle in ("workspace only", "no stable", "no promotion", "human-approved",
                   "fixed test command allowlist"):
        if needle not in combined and needle.replace("-", " ") not in combined:
            errors.append(f"approved-apply docs missing phrase: {needle!r}")

    # Functional: the apply validator rejects unapproved / stable-target / shell /
    # applied proposals so no apply code can touch stable.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from src.repair.apply_validator import ApprovalRecord, validate_for_apply
        from src.repair.types import RepairAction, RepairProposal

        def _mk(action_type="update_candidate", target="harnesses/candidates/c/"):
            return RepairProposal(id="p", failure_type="test_failed", actions=[
                RepairAction(id="a", action_type=action_type, target=target)])

        approved = ApprovalRecord(approved=True, reviewer="h")
        if validate_for_apply(_mk(), ApprovalRecord(approved=False, reviewer="h")).valid:
            errors.append("apply validator accepted a missing approval marker")
        if validate_for_apply(_mk(target="skills/x/"), approved).valid:
            errors.append("apply validator accepted a stable target")
        if validate_for_apply(_mk(action_type="raw_shell"), approved).valid:
            errors.append("apply validator accepted a raw_shell action")
        if validate_for_apply(_mk(target="src/agents/safety_gate/x.py"), approved).valid:
            errors.append("apply validator accepted a safety_gate target")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"approved-apply functional check failed: {exc}")
    return errors


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

    # NOTE: Phase 3 froze "no repair_apply.py" at commit b1ffd56 (a historical
    # snapshot, still recorded in the checkpoint doc). Phase 4 (Approved Patch
    # Application) intentionally adds a workspace-only repair_apply.py — gated by
    # _approved_apply_errors — so we no longer assert its absence here.

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

    # repair_propose.py itself must stay proposal-only — its --apply is rejected.
    # (Approved apply lives in a separate, human-approved script: repair_apply.py,
    # gated by the Phase 4 approved-apply contract — see _approved_apply_errors.)
    rp = root / "scripts" / "repair_propose.py"
    if rp.exists() and "--apply" not in rp.read_text(encoding="utf-8"):
        errors.append("repair_propose.py no longer documents/rejects --apply")

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


def _real_provider_safety_errors(root: Path) -> list[str]:
    """Real providers exist but stay safe: fake default, fail-closed, env-var-name
    only, no file/secret read, redacted, no real call by default."""
    errors: list[str] = []
    required = [
        "src/llm/openai_provider.py",
        "src/llm/anthropic_provider.py",
        "scripts/llm_provider_smoke.py",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing path: {rel}")

    # Provider source: stdlib only, key from named env var, no file/secret read.
    for rel in ("src/llm/openai_provider.py", "src/llm/anthropic_provider.py"):
        p = root / rel
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        if "os.environ.get(self.api_key_env)" not in src:
            errors.append(f"{rel}: must read the key only from the named env var")
        if "open(" in src.replace("urlopen", ""):
            errors.append(f"{rel}: must not open a local file (no .env/password read)")
        for pkg in ("import requests", "import httpx", "import aiohttp"):
            if pkg in src:
                errors.append(f"{rel}: must not import a heavy HTTP client ({pkg})")
        if "redact" not in src:
            errors.append(f"{rel}: must redact output")

    # smoke script must default to dry-run / no real call and gate --real-call.
    sm = root / "scripts" / "llm_provider_smoke.py"
    if sm.exists():
        s = sm.read_text(encoding="utf-8")
        if "--real-call" not in s or "--dry-run" not in s:
            errors.append("llm_provider_smoke.py must offer --dry-run (default) and gate --real-call")

    # Functional: fake is default; real provider fails closed unless allowed.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from src.llm import build_provider, LLMProviderError, FakeLLMProvider
        if not isinstance(build_provider(config={"llm": {"provider": "fake"}}), FakeLLMProvider):
            errors.append("default provider is not fake")
        try:
            build_provider(config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                                           "allow_real_api_calls": False}})
            errors.append("real provider not fail-closed when allow_real_api_calls=false")
        except LLMProviderError:
            pass
        # allowed -> constructs without reading a key value / making a call
        prov = build_provider(config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                                              "allow_real_api_calls": True}})
        if not getattr(prov, "real_api_enabled", False) or getattr(prov, "api_key_env", "") != "OPENAI_API_KEY":
            errors.append("allowed real provider did not construct correctly")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"real provider functional check failed: {exc}")
    return errors


def _test_environment_baseline_errors(root: Path) -> list[str]:
    """The test-environment baseline is documented and the checker exists and agrees
    with the doc on the known environment-gap tests. SOFT: env gaps (missing
    `python` on PATH / .venv / Playwright) are printed as warnings and do NOT fail
    the gate; only a missing doc/script or a checker crash is an error. Makes no real
    API call, installs nothing, reads no secret."""
    errors: list[str] = []
    doc = root / "docs" / "test_environment_baseline.md"
    script = root / "scripts" / "check_test_environment_baseline.py"
    for rel, p in (("docs/test_environment_baseline.md", doc),
                   ("scripts/check_test_environment_baseline.py", script)):
        if not p.exists():
            errors.append(f"missing path: {rel}")
    if errors:
        return errors

    # Doc must cover the required topics (kept in sync with the story requirements).
    dt = doc.read_text(encoding="utf-8").lower()
    for needle in ("system python", ".venv", "playwright",
                   "regression vs environment gap", ".venv/bin/python",
                   "environment gap"):
        if needle not in dt:
            errors.append(f"test_environment_baseline.md missing topic: {needle!r}")

    # Script must be report-only: it must never install / download, and a missing
    # `python` must be a warning, not a failure.
    ss = script.read_text(encoding="utf-8")
    for forbidden in ("pip install", "playwright install", "urllib.request", "urlopen"):
        if forbidden in ss:
            errors.append(f"baseline checker must not {forbidden!r} (no install/network)")
    if "WARNING only" not in ss and "warning only" not in ss.lower():
        errors.append("baseline checker must treat missing `python` as a warning only")

    # Load and run the checker; it must NOT raise and must NOT exit non-zero in its
    # default (report) mode even when `python` is missing from PATH.
    try:
        spec = importlib.util.spec_from_file_location("check_test_environment_baseline", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        summary = mod.gather(root)
        warns = mod.warnings_for(summary)
        # The doc and the checker must list the SAME known env-gap tests.
        for t in mod.KNOWN_ENV_GAP_TESTS:
            if t not in doc.read_text(encoding="utf-8"):
                errors.append(f"baseline doc missing known env-gap test: {t}")
        rc = mod.main([])  # default report mode
        if rc != 0:
            errors.append(f"baseline checker default mode exited {rc} (must be 0; warning-only)")
        # Surface the baseline + warnings as INFO (never a failure here).
        print("[baseline] test environment:"
              f" venv={'yes' if summary['venv_python_exists'] else 'no'},"
              f" real_browser_path={'yes' if summary['real_browser_path_available'] else 'no'},"
              f" python_on_PATH={'yes' if summary['python_on_path'] else 'no (warning only)'}")
        for w in warns:
            print(f"  [WARN] {w}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"baseline checker crashed: {exc}")
    return errors


def _openai_readonly_execution_errors(root: Path) -> list[str]:
    """OpenAI Read-Only Plan Execution Gate v0 stays safe: gate module + script +
    eval + tests + the approved fixture exist; dry-run executes nothing; a real run
    requires --approved + the approval marker + a reviewer + a valid allowlisted plan;
    ONLY inspect_project is allowlisted; non-read-only skills are refused; no shell,
    no repair/promotion, no replan/auto-repair; results are redacted. The execution
    script makes NO OpenAI call. No real API call is made by this check."""
    errors: list[str] = []
    gate = root / "src" / "planner" / "read_only_execution_gate.py"
    script = root / "scripts" / "execute_openai_readonly_plan.py"
    test = root / "tests" / "unit" / "test_openai_readonly_execution_gate.py"
    eval_yaml = root / "evals" / "planner" / "openai_readonly_plan_execution.yaml"
    fixture = root / "fixtures" / "openai_planner" / "approved_readonly_plan"
    for rel, p in (("src/planner/read_only_execution_gate.py", gate),
                   ("scripts/execute_openai_readonly_plan.py", script),
                   ("tests/unit/test_openai_readonly_execution_gate.py", test),
                   ("evals/planner/openai_readonly_plan_execution.yaml", eval_yaml),
                   ("fixtures/openai_planner/approved_readonly_plan/plan.json",
                    fixture / "plan.json"),
                   ("fixtures/openai_planner/approved_readonly_plan/approval_checklist.md",
                    fixture / "approval_checklist.md")):
        if not p.exists():
            errors.append(f"missing path: {rel}")

    if gate.exists():
        g = gate.read_text(encoding="utf-8")
        for forbidden in ("import subprocess", "subprocess.run", "os.system", "shell=True",
                          "from src.repair", "import staging_promote",
                          "build_execution_sequence"):
            if forbidden in g:
                errors.append(f"gate must not use {forbidden!r} (read-only, no shell/repair)")
        if "redact" not in g:
            errors.append("gate must redact results")

    if script.exists():
        s = script.read_text(encoding="utf-8")
        if "--approved" not in s or "--dry-run" not in s:
            errors.append("execute script must offer --dry-run (default) and gate --approved")
        # The execution script must NOT call OpenAI or read the key.
        for forbidden in ("build_provider", "build_planner_from_config", "os.environ",
                          "real-call", "--real-call"):
            if forbidden in s:
                errors.append(f"execute script must not {forbidden!r} (no OpenAI call here)")

    # Functional: allowlist is inspect_project-only; non-read-only skills refused;
    # authorization requires marker + reviewer + approved + valid plan; execution of a
    # forbidden skill is refused even when 'approved'. No real API call.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from src.planner.read_only_execution_gate import (
            READONLY_ALLOWLIST, ApprovalRecord, ReadOnlyExecutionError,
            authorize, execute_readonly_plan, validate_readonly_plan,
        )
        from src.planner.types import Plan, PlanStep

        if READONLY_ALLOWLIST != ("inspect_project",):
            errors.append("read-only allowlist drifted from ('inspect_project',)")

        clean = Plan(goal="g", steps=[PlanStep(id="i", skill="inspect_project", risk_level="low")])
        if not validate_readonly_plan(clean).ok:
            errors.append("gate rejected a clean inspect_project plan")
        approved = ApprovalRecord(approved_marker=True, reviewer="r")
        if not authorize(clean, approved, approved=True).ok:
            errors.append("gate did not authorize a fully-approved clean plan")
        # missing any condition -> not authorized
        if authorize(clean, approved, approved=False).ok:
            errors.append("gate authorized without --approved")
        if authorize(clean, ApprovalRecord(approved_marker=False, reviewer="r"), approved=True).ok:
            errors.append("gate authorized without the approval marker")
        if authorize(clean, ApprovalRecord(approved_marker=True, reviewer=""), approved=True).ok:
            errors.append("gate authorized without a reviewer")
        # forbidden skills refused
        for skill in ("patch_file_and_run_tests", "start_local_server",
                      "open_localhost_browser", "read_browser_console", "raw_shell"):
            bad = Plan(goal="g", steps=[PlanStep(id="x", skill=skill, risk_level="low")])
            if validate_readonly_plan(bad).ok:
                errors.append(f"gate accepted a non-read-only skill: {skill}")
            try:
                execute_readonly_plan(bad, approved, approved=True, project_dir=str(root))
                errors.append(f"gate executed a non-read-only skill: {skill}")
            except ReadOnlyExecutionError:
                pass
    except Exception as exc:  # noqa: BLE001
        errors.append(f"read-only gate functional check failed: {exc}")
    return errors


def _openai_plan_review_errors(root: Path) -> list[str]:
    """OpenAI Plan Review Package v0 stays review-only: the generator + tests +
    committed example exist; the package marks NOT APPROVED / PLAN NOT EXECUTED /
    HUMAN APPROVAL REQUIRED; a non-low-risk or non-allowlisted plan is BLOCKED; and
    nothing is executed or auto-repaired. No real API call is made by this check."""
    errors: list[str] = []
    script = root / "scripts" / "openai_plan_review.py"
    test = root / "tests" / "unit" / "test_openai_plan_review.py"
    readme = root / "reports" / "openai_plan_review_v0" / "README.md"
    example = root / "reports" / "openai_plan_review_v0" / "example"
    for rel, p in (("scripts/openai_plan_review.py", script),
                   ("tests/unit/test_openai_plan_review.py", test),
                   ("reports/openai_plan_review_v0/README.md", readme)):
        if not p.exists():
            errors.append(f"missing path: {rel}")

    if script.exists():
        s = script.read_text(encoding="utf-8")
        if "--real-call" not in s or "--dry-run" not in s:
            errors.append("plan review must offer --dry-run (default) and gate --real-call")
        if "os.environ.get(API_KEY_ENV)" not in s:
            errors.append("plan review must read the key only from the named env var")
        if "open(" in s.replace("urlopen", ""):
            errors.append("plan review must not open a local secret file")
        if "redact" not in s or "validate_plan" not in s:
            errors.append("plan review must validate the plan and redact artifacts")
        for forbidden in ("build_execution_sequence", "from src.repair", "staging_promote"):
            if forbidden in s:
                errors.append(f"plan review must not use {forbidden!r} (review-only)")

    # The committed example must be REVIEW-READY and NOT approved by default.
    for name in ("plan.json", "plan_summary.md", "risk_assessment.md",
                 "approval_checklist.md", "execution_preconditions.md", "review_report.json"):
        if not (example / name).exists():
            errors.append(f"missing example artifact: reports/openai_plan_review_v0/example/{name}")
    chk = example / "approval_checklist.md"
    if chk.exists():
        t = chk.read_text(encoding="utf-8")
        for needle in ("NOT APPROVED BY DEFAULT", "PLAN NOT EXECUTED",
                       "HUMAN APPROVAL REQUIRED", "APPROVED_FOR_READONLY_EXECUTION: false"):
            if needle not in t:
                errors.append(f"example approval_checklist missing: {needle!r}")

    # Functional: a forbidden/elevated plan is BLOCKED by the risk assessment.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("openai_plan_review", script)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        from src.planner.types import Plan, PlanStep
        clean = Plan(goal="g", steps=[PlanStep(id="a", skill="inspect_project", risk_level="low")])
        if mod.assess_risk(clean)["blocked_reasons"]:
            errors.append("review wrongly blocked a clean inspect_project plan")
        bad = Plan(goal="g", steps=[PlanStep(id="a", skill="patch_file_and_run_tests",
                                             risk_level="low")])
        if not mod.assess_risk(bad)["blocked_reasons"]:
            errors.append("review failed to block a non-allowlisted skill")
        med = Plan(goal="g", steps=[PlanStep(id="a", skill="inspect_project", risk_level="medium")])
        if not mod.assess_risk(med)["blocked_reasons"]:
            errors.append("review failed to block a non-low-risk step")
        if mod.READONLY_SKILL_ALLOWLIST != ("inspect_project",):
            errors.append("review read-only allowlist drifted from ('inspect_project',)")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"plan review functional check failed: {exc}")
    return errors


def _openai_planner_live_plan_errors(root: Path) -> list[str]:
    """The OpenAI live planner stays safe: plan-only, dry-run default, --real-call
    gated, FIXED system prompt (no file/browser/trace content), the plan must pass
    PlanValidator or be BLOCKED (no auto-repair), and all artifacts are redacted. It
    reads the key only from the named env var and makes NO real API call in this
    check (dry-run only)."""
    errors: list[str] = []
    script = root / "scripts" / "openai_planner_live_plan.py"
    test = root / "tests" / "unit" / "test_openai_planner_live_plan_script.py"
    eval_yaml = root / "evals" / "planner" / "openai_live_plan_only_blocked_or_passed.yaml"
    for rel, p in (("scripts/openai_planner_live_plan.py", script),
                   ("tests/unit/test_openai_planner_live_plan_script.py", test),
                   ("evals/planner/openai_live_plan_only_blocked_or_passed.yaml", eval_yaml)):
        if not p.exists():
            errors.append(f"missing path: {rel}")

    if script.exists():
        s = script.read_text(encoding="utf-8")
        if "--real-call" not in s or "--dry-run" not in s:
            errors.append("live planner must offer --dry-run (default) and gate --real-call")
        if "os.environ.get(API_KEY_ENV)" not in s:
            errors.append("live planner must read the key only from the named env var")
        if "open(" in s.replace("urlopen", ""):
            errors.append("live planner must not open a local file (no .env/password read)")
        if "redact" not in s:
            errors.append("live planner must redact output / artifacts")
        if "validate_plan" not in s:
            errors.append("live planner must validate the plan with PlanValidator")
        # plan-only: it must not import an executor / repair / promotion runtime
        for forbidden in ("execution_bridge", "src.repair", "staging_promote", "execute_plan"):
            if forbidden in s:
                errors.append(f"live planner must not use {forbidden!r} (plan-only)")

    if eval_yaml.exists():
        t = eval_yaml.read_text(encoding="utf-8")
        for needle in ("planner_provider_live", "plan_not_executed", "no_auto_repair",
                       "no_secret_in_plan", "plan_valid_or_blocked"):
            if needle not in t:
                errors.append(f"openai_live_plan_only_blocked_or_passed.yaml missing: {needle}")

    # Functional: live_plan is fail-closed (refuses a non-real provider / no opt-in)
    # and the parser+validator reject a forbidden skill. No real API call here.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        import json as _json
        from src.llm.fake_provider import FakeLLMProvider
        from src.planner.provider_planner import (
            LivePlanError, ProviderBackedPlanner, parse_plan_from_text,
        )
        from src.planner.plan_validator import validate_plan
        from src.planner.types import PlannerRequest

        # fake provider -> live_plan refused (never reaches a real API)
        try:
            ProviderBackedPlanner(FakeLLMProvider(), allow_real_call=True).live_plan(
                PlannerRequest(goal="x"))
            errors.append("live_plan accepted a non-real provider")
        except LivePlanError:
            pass
        # a forbidden-skill plan from the parser must fail validation (blocked, not fixed)
        bad = parse_plan_from_text(_json.dumps({"steps": [{"id": "a", "skill": "raw_shell"}]}), "g")
        if validate_plan(bad).valid:
            errors.append("validator accepted a forbidden-skill live plan")
        # non-JSON output -> LivePlanError
        try:
            parse_plan_from_text("not json at all", "g")
            errors.append("parser accepted non-JSON output")
        except LivePlanError:
            pass
    except Exception as exc:  # noqa: BLE001
        errors.append(f"live planner functional check failed: {exc}")
    return errors


def _real_provider_live_smoke_errors(root: Path) -> list[str]:
    """The OpenAI live smoke stays safe: dry-run default, --real-call gated, a FIXED
    prompt (no arbitrary prompt), redacted output/reports, fail-closed without the
    env var, and OpenAI-only this round (Anthropic blocked / not tested). It reads
    the key only from the named env var, never opens a secret file, and makes NO real
    API call in this check (dry-run only)."""
    errors: list[str] = []
    script = root / "scripts" / "real_provider_live_smoke.py"
    test = root / "tests" / "unit" / "test_real_provider_live_smoke_script.py"
    for rel, p in (("scripts/real_provider_live_smoke.py", script),
                   ("tests/unit/test_real_provider_live_smoke_script.py", test)):
        if not p.exists():
            errors.append(f"missing path: {rel}")

    if script.exists():
        s = script.read_text(encoding="utf-8")
        if "--real-call" not in s or "--dry-run" not in s:
            errors.append("live smoke must offer --dry-run (default) and gate --real-call")
        if "Reply with exactly: provider-ok" not in s:
            errors.append("live smoke must use the FIXED smoke prompt (no arbitrary prompt)")
        if "os.environ.get(api_key_env)" not in s:
            errors.append("live smoke must read the key only from the named env var")
        if "open(" in s.replace("urlopen", ""):
            errors.append("live smoke must not open a local file (no .env/password read)")
        if "redact" not in s:
            errors.append("live smoke must redact output / reports")
        # The live smoke must not actually run a planner / plan execution / auto-repair
        # / stable promotion — assert it imports none of those runtimes.
        for forbidden in ("src.planner", "execute_plan", "src.repair", "staging_promote"):
            if forbidden in s:
                errors.append(f"live smoke must not use {forbidden!r} (out of scope)")

    # Functional dry-run: OpenAI constructs without a key and makes no call; a
    # real-call WITHOUT the env var is blocked (exit 2). No real API call here.
    import json as _json
    import os as _os
    import subprocess as _subprocess
    import sys as _sys
    import tempfile as _tempfile

    if script.exists():
        env_no_key = {k: v for k, v in _os.environ.items()
                      if k not in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")}
        with _tempfile.TemporaryDirectory() as tmp:
            try:
                dry = _subprocess.run(
                    [_sys.executable, str(script), "--provider", "openai", "--dry-run",
                     "--out-dir", tmp], capture_output=True, text=True, cwd=str(root),
                    env=env_no_key)
                if dry.returncode != 0:
                    errors.append(f"live smoke dry-run did not exit 0 (got {dry.returncode})")
                else:
                    data = _json.loads(dry.stdout)
                    if data.get("real_api_called") is not False:
                        errors.append("live smoke dry-run reported a real API call")
                    if data.get("api_key_env") != "OPENAI_API_KEY":
                        errors.append("live smoke dry-run lost the env-var NAME")
                blocked = _subprocess.run(
                    [_sys.executable, str(script), "--provider", "openai", "--real-call",
                     "--out-dir", tmp], capture_output=True, text=True, cwd=str(root),
                    env=env_no_key)
                if blocked.returncode != 2:
                    errors.append("live smoke --real-call without the env var was not blocked (exit 2)")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"live smoke functional check failed: {exc}")
    return errors


def _planner_provider_integration_errors(root: Path) -> list[str]:
    """Provider-aware planner stays safe: fake default, real fail-closed without
    opt-in, real provider HELD but never called in a dry-run, plan-only, redacted.
    No real API call is made by this check."""
    errors: list[str] = []
    required = [
        "src/planner/provider_planner.py",
        "scripts/planner_provider_smoke.py",
        "evals/planner/provider_backed_plan_dry_run.yaml",
        "tests/unit/test_planner_provider_integration.py",
        "tests/unit/test_planner_provider_smoke_script.py",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing planner-provider path: {rel}")

    # Source: the planner never reads an env-var VALUE or opens a secret file; the
    # provider reads its key only at call time (and we never call it in a dry-run).
    pp = root / "src" / "planner" / "provider_planner.py"
    if pp.exists():
        src = pp.read_text(encoding="utf-8")
        if "os.environ" in src or "getenv" in src:
            errors.append("provider_planner.py must not read an env-var value")
        if "open(" in src:
            errors.append("provider_planner.py must not open a local file")
        if "redact" not in src:
            errors.append("provider_planner.py must redact provider output")

    # The smoke script is dry-run only — it must NOT carry a real-call path.
    sm = root / "scripts" / "planner_provider_smoke.py"
    if sm.exists():
        s = sm.read_text(encoding="utf-8")
        if "--real-call" in s:
            errors.append("planner_provider_smoke.py must not expose a real-call path")
        if "--dry-run" not in s:
            errors.append("planner_provider_smoke.py must offer --dry-run")

    # The dry-run eval must not be wired to execute or call a real API.
    ev = root / "evals" / "planner" / "provider_backed_plan_dry_run.yaml"
    if ev.exists():
        t = ev.read_text(encoding="utf-8")
        for needle in ("planner_provider_dry_run", "no_real_api_call", "plan_not_executed"):
            if needle not in t:
                errors.append(f"provider_backed_plan_dry_run.yaml missing: {needle}")

    # Functional: fake is default; real fails closed without opt-in; under opt-in the
    # provider is HELD and a dry-run plan is built WITHOUT calling it.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from src.llm import LLMProviderError
        from src.planner.provider_planner import (
            ProviderBackedPlanner, build_planner_from_config,
        )
        from src.planner.plan_validator import validate_plan
        from src.planner.types import PlannerRequest

        fake = build_planner_from_config(config={"llm": {"provider": "fake"}}, root=root)
        if fake.provider_name != "fake" or fake.real_api_enabled:
            errors.append("provider-backed default is not the fake provider")

        try:
            build_planner_from_config(
                config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                                "allow_real_api_calls": False}}, root=root)
            errors.append("provider-backed planner not fail-closed without opt-in")
        except LLMProviderError:
            pass

        held = build_planner_from_config(
            config={"llm": {"provider": "openai", "api_key_env": "OPENAI_API_KEY",
                            "allow_real_api_calls": True}}, root=root, allow_real_call=False)
        if not held.real_api_enabled or held.allow_real_call:
            errors.append("opted-in real provider should be HELD (allow_real_call=False)")

        # A real provider stub whose complete() raises proves the dry-run never calls it.
        class _NoCall:
            provider_name = "openai"
            real_api_enabled = True
            model = ""

            def complete(self, request):  # noqa: D401
                raise AssertionError("real provider called in dry-run")

        resp = ProviderBackedPlanner(_NoCall(), allow_real_call=False).plan(
            PlannerRequest(marker="FAKE_PLAN_FULL_BROWSER_E2E"))
        if not validate_plan(resp.plan).valid:
            errors.append("provider-backed dry-run produced an invalid plan")
        if "not called" not in resp.raw_response_redacted:
            errors.append("dry-run did not hold the real provider (it may have been called)")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"planner-provider functional check failed: {exc}")
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
