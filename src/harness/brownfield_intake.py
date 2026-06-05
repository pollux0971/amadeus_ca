from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

from src.harness.source_manifest import ExternalSourceManifest, requires_human_review, validate_manifest


@dataclass
class IntakePlan:
    source_id: str
    current_status: str
    next_status: str
    required_actions: list[str]
    human_review_required: bool
    errors: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


SOURCE_TYPE_ACTIONS = {
    "repo": ["inspect_license", "inspect_package_scripts", "propose_adapter", "run_tests_in_sandbox"],
    "dataset": ["compute_schema", "sample_rows", "create_artifact_refs", "write_data_channel_eval"],
    "document": ["extract_metadata", "chunk_or_page_index", "create_evidence_refs"],
    "image": ["compute_hash", "extract_metadata", "create_image_artifact_ref"],
    "audio": ["compute_hash", "extract_metadata", "transcribe_or_summarize_if_allowed"],
    "video": ["compute_hash", "extract_metadata", "sample_frames_if_allowed"],
    "sensor_stream": ["compute_schema", "window_statistics", "detect_anomalies"],
    "ui_prototype": ["isolate_under_apps", "write_api_contract", "create_ui_eval"],
}


def classify_path(path: Path) -> str:
    if path.is_dir():
        if (path / "package.json").exists() or (path / "pyproject.toml").exists() or (path / ".git").exists():
            return "repo"
        return "dataset"
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return "image"
    if suffix in {".pdf", ".docx", ".md", ".txt"}:
        return "document"
    if suffix in {".csv", ".json", ".jsonl", ".parquet"}:
        return "dataset"
    if suffix in {".wav", ".mp3", ".m4a", ".flac"}:
        return "audio"
    if suffix in {".mp4", ".mov", ".mkv"}:
        return "video"
    return "archive"


def plan_intake(manifest: ExternalSourceManifest, project_root: Path | None = None) -> IntakePlan:
    errors = validate_manifest(manifest, project_root)
    actions = ["manifest_gate"]
    actions.extend(SOURCE_TYPE_ACTIONS.get(manifest.source_type, ["manual_review"]))
    actions.extend(["safety_gate", "adapter_gate", "eval_gate", "promotion_gate"])
    next_status = "quarantined" if not errors else manifest.review_status
    return IntakePlan(
        source_id=manifest.source_id,
        current_status=manifest.review_status,
        next_status=next_status,
        required_actions=actions,
        human_review_required=requires_human_review(manifest),
        errors=errors,
    )
