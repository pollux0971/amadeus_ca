from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.harness.multimodal_artifacts import ArtifactRef, create_artifact_ref
from src.harness.source_manifest import ExternalSourceManifest


class DataChannelAdapter(ABC):
    channel_id: str

    @abstractmethod
    def can_handle(self, manifest: ExternalSourceManifest) -> bool:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, manifest: ExternalSourceManifest, project_root: Path) -> list[ArtifactRef]:
        raise NotImplementedError


class LocalFileDataChannel(DataChannelAdapter):
    channel_id = "local_file"

    def can_handle(self, manifest: ExternalSourceManifest) -> bool:
        return manifest.source_type in {"dataset", "document", "image", "audio", "video", "sensor_stream", "repo"}

    def normalize(self, manifest: ExternalSourceManifest, project_root: Path) -> list[ArtifactRef]:
        path = (project_root / manifest.location).resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        if path.is_dir() and manifest.source_type != "repo":
            return [create_artifact_ref(manifest.source_id, child, manifest.trust_level) for child in sorted(path.iterdir()) if child.is_file()]
        return [create_artifact_ref(manifest.source_id, path, manifest.trust_level)]
