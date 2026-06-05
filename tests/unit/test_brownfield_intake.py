from pathlib import Path

from src.harness.brownfield_intake import classify_path, plan_intake
from src.harness.source_manifest import ExternalSourceManifest


def test_classify_repo_fixture():
    fixture = Path("fixtures/open_source_project_sample")
    assert classify_path(fixture) == "repo"


def test_plan_intake_for_repo_includes_sandbox_actions():
    manifest = ExternalSourceManifest(
        source_id="repo_001",
        source_type="repo",
        origin="github",
        location="external/inbox/raw/repo_001",
        trust_level="third_party_open_source",
        intended_use=["reference_implementation"],
        allowed_operations=["read_files", "run_tests_in_sandbox"],
    )
    plan = plan_intake(manifest)
    assert plan.next_status == "quarantined"
    assert "inspect_package_scripts" in plan.required_actions
    assert plan.human_review_required
