from pathlib import Path

from src.harness.data_channel import LocalFileDataChannel
from src.harness.multimodal_artifacts import create_artifact_ref, infer_artifact_type, should_inject_raw
from src.harness.source_manifest import ExternalSourceManifest


def test_infer_artifact_type_csv():
    assert infer_artifact_type(Path("data.csv")) == "csv"


def test_create_artifact_ref_preserves_raw_ref():
    path = Path("fixtures/data_channel_samples/sample.csv")
    artifact = create_artifact_ref("sample_csv", path)
    assert artifact.artifact_type == "csv"
    assert artifact.raw_ref.endswith("sample.csv")
    assert artifact.sha256 is not None


def test_does_not_inject_raw_images_by_default():
    artifact = create_artifact_ref("fake_image", Path("fixtures/multimodal_samples/README.md"))
    # Text may be injectable when trusted, but untrusted sources should not be injected raw.
    artifact.trust_level = "untrusted_web"
    assert not should_inject_raw(artifact, 10_000)


def test_local_file_channel_normalizes_csv():
    manifest = ExternalSourceManifest(
        source_id="sample_csv",
        source_type="dataset",
        origin="fixture",
        location="fixtures/data_channel_samples/sample.csv",
        trust_level="user_provided",
        intended_use=["test"],
        allowed_operations=["read_files"],
    )
    channel = LocalFileDataChannel()
    artifacts = channel.normalize(manifest, Path.cwd())
    assert len(artifacts) == 1
    assert artifacts[0].artifact_type == "csv"
