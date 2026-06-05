from __future__ import annotations

from dataclasses import dataclass, field, asdict
from hashlib import sha256
from pathlib import Path
from typing import Literal

ArtifactType = Literal["text", "csv", "json", "pdf", "image", "audio", "video", "sensor", "repo", "web_capture"]


@dataclass
class ArtifactRef:
    artifact_id: str
    source_id: str
    artifact_type: ArtifactType
    uri: str
    trust_level: str
    summary: str = ""
    sha256: str | None = None
    mime_type: str | None = None
    metadata: dict = field(default_factory=dict)
    raw_ref: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def file_sha256(path: Path, max_bytes: int | None = None) -> str:
    h = sha256()
    with path.open("rb") as f:
        remaining = max_bytes
        while True:
            if remaining is not None and remaining <= 0:
                break
            chunk_size = 1024 * 1024 if remaining is None else min(1024 * 1024, remaining)
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
            if remaining is not None:
                remaining -= len(chunk)
    return h.hexdigest()


def infer_artifact_type(path: Path) -> ArtifactType:
    if path.is_dir():
        return "repo"
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return "image"
    if suffix in {".wav", ".mp3", ".m4a", ".flac"}:
        return "audio"
    if suffix in {".mp4", ".mov", ".mkv"}:
        return "video"
    if suffix == ".csv":
        return "csv"
    if suffix in {".json", ".jsonl"}:
        return "json"
    return "text"


def create_artifact_ref(source_id: str, path: Path, trust_level: str = "user_provided") -> ArtifactRef:
    artifact_type = infer_artifact_type(path)
    digest = None if path.is_dir() else file_sha256(path, max_bytes=10 * 1024 * 1024)
    return ArtifactRef(
        artifact_id=f"{source_id}:{path.name}",
        source_id=source_id,
        artifact_type=artifact_type,
        uri=str(path),
        trust_level=trust_level,
        summary=f"{artifact_type} artifact from {path.name}",
        sha256=digest,
        raw_ref=str(path),
        metadata={"name": path.name, "is_dir": path.is_dir()},
    )


def should_inject_raw(artifact: ArtifactRef, context_budget_tokens: int) -> bool:
    """Default conservative policy for context injection."""
    if artifact.artifact_type in {"image", "audio", "video", "pdf", "repo"}:
        return False
    if artifact.trust_level in {"untrusted_web", "third_party_open_source", "sensitive_private"}:
        return False
    return context_budget_tokens >= 2000
