from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

ALLOWED_SOURCE_TYPES = {
    "repo",
    "archive",
    "dataset",
    "document",
    "image",
    "audio",
    "video",
    "sensor_stream",
    "ui_prototype",
    "api_spec",
    "browser_capture",
}

ALLOWED_TRUST_LEVELS = {
    "trusted_local",
    "user_provided",
    "third_party_open_source",
    "untrusted_web",
    "sensitive_private",
}

ALLOWED_REVIEW_STATUS = {
    "manifested",
    "quarantined",
    "normalized",
    "staged",
    "tested",
    "approved",
    "rejected",
    "deprecated",
}


@dataclass
class ExternalSourceManifest:
    """Machine-readable metadata for a brownfield source.

    The harness should not consume arbitrary files directly. A manifest describes a source,
    its trust boundary, allowed operations, and intended use before adapters can process it.
    """

    source_id: str
    source_type: str
    origin: str
    location: str
    trust_level: str
    intended_use: list[str]
    allowed_operations: list[str]
    review_status: str = "manifested"
    forbidden_operations: list[str] = field(default_factory=list)
    license: str | None = None
    owner: str | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def validate_manifest(manifest: ExternalSourceManifest, project_root: Path | None = None) -> list[str]:
    """Return validation errors. Empty list means valid enough for intake."""
    errors: list[str] = []
    if not manifest.source_id.strip():
        errors.append("source_id is required")
    if manifest.source_type not in ALLOWED_SOURCE_TYPES:
        errors.append(f"unsupported source_type: {manifest.source_type}")
    if manifest.trust_level not in ALLOWED_TRUST_LEVELS:
        errors.append(f"unsupported trust_level: {manifest.trust_level}")
    if manifest.review_status not in ALLOWED_REVIEW_STATUS:
        errors.append(f"unsupported review_status: {manifest.review_status}")
    if not manifest.intended_use:
        errors.append("intended_use must not be empty")
    if not manifest.allowed_operations:
        errors.append("allowed_operations must not be empty")
    if ".." in Path(manifest.location).parts:
        errors.append("location must not contain parent traversal")
    if project_root is not None:
        try:
            resolved = (project_root / manifest.location).resolve()
            root_resolved = project_root.resolve()
            if root_resolved not in resolved.parents and resolved != root_resolved:
                errors.append("location must stay inside project root")
        except OSError as exc:
            errors.append(f"location resolution failed: {exc}")
    return errors


def requires_human_review(manifest: ExternalSourceManifest) -> bool:
    risky_ops = {
        "execute_shell",
        "execute_install_scripts",
        "network_access",
        "read_private_data",
        "camera_input",
        "microphone_input",
        "modify_safety_policy",
    }
    if manifest.trust_level in {"untrusted_web", "sensitive_private", "third_party_open_source"}:
        return True
    return any(op in risky_ops for op in manifest.allowed_operations)


def summarize_manifest(manifest: ExternalSourceManifest) -> str:
    review = "human-review-required" if requires_human_review(manifest) else "auto-review-eligible"
    return f"{manifest.source_id} ({manifest.source_type}, {manifest.trust_level}) -> {review}"
