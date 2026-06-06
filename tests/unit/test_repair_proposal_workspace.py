import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.repair.candidate_workspace import create_workspace
from src.repair.fake_repair_planner import FakeRepairPlanner, MARKER_TEST_FAILED
from src.repair.proposal_validator import validate_proposal
from src.repair.types import FailureAnalysis


def _make():
    analysis = FailureAnalysis(run_ref="x", failure_type="test_failed",
                               unmet_criteria=["tests_pass"])
    proposal = FakeRepairPlanner().propose(analysis, marker=MARKER_TEST_FAILED)
    validation = validate_proposal(proposal)
    return analysis, proposal, validation


def test_workspace_created_and_files_written():
    analysis, proposal, validation = _make()
    with tempfile.TemporaryDirectory() as d:
        plan = create_workspace(proposal, analysis, validation, base_dir=d)
        ws = Path(plan.workspace_dir)
        assert ws.exists()
        for f in ("repair_proposal.json", "repair_proposal.md",
                  "failure_analysis.json", "approval_checklist.md", "README.md"):
            assert (ws / f).exists(), f
            assert f in plan.files_written
        assert plan.applied is False


def test_proposal_only_readme_and_checklist_exist():
    analysis, proposal, validation = _make()
    with tempfile.TemporaryDirectory() as d:
        plan = create_workspace(proposal, analysis, validation, base_dir=d)
        ws = Path(plan.workspace_dir)
        readme = (ws / "README.md").read_text(encoding="utf-8").lower()
        assert "proposal only" in readme
        assert "no target file was modified" in readme
        checklist = (ws / "approval_checklist.md").read_text(encoding="utf-8").lower()
        assert "approval checklist" in checklist
        assert "human" in checklist
        # proposal json marked not applied
        doc = json.loads((ws / "repair_proposal.json").read_text(encoding="utf-8"))
        assert doc["applied"] is False


def test_target_files_not_modified():
    # the workspace must only create files under its own dir, never touch a target
    analysis, proposal, validation = _make()
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        # create a sentinel "target" that must remain untouched
        target = base / "harnesses_candidates_x"
        target.mkdir()
        sentinel = target / "candidate.yaml"
        sentinel.write_text("original", encoding="utf-8")
        plan = create_workspace(proposal, analysis, validation, base_dir=base)
        # only the workspace subdir was written; the sentinel is unchanged
        assert sentinel.read_text(encoding="utf-8") == "original"
        assert Path(plan.workspace_dir).parent == base


def test_workspace_has_no_secret():
    from src.llm.redaction import redact_text
    analysis, proposal, validation = _make()
    with tempfile.TemporaryDirectory() as d:
        plan = create_workspace(proposal, analysis, validation, base_dir=d)
        for f in Path(plan.workspace_dir).iterdir():
            text = f.read_text(encoding="utf-8")
            assert redact_text(text) == text  # no secret pattern present


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
