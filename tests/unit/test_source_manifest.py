from pathlib import Path

from src.harness.source_manifest import ExternalSourceManifest, requires_human_review, validate_manifest


def test_manifest_validation_accepts_known_source_type():
    manifest = ExternalSourceManifest(
        source_id="csv_001",
        source_type="dataset",
        origin="user_upload",
        location="external/inbox/raw/sample.csv",
        trust_level="user_provided",
        intended_use=["data_channel_test"],
        allowed_operations=["read_files"],
    )
    assert validate_manifest(manifest, Path.cwd()) == []


def test_manifest_blocks_path_traversal():
    manifest = ExternalSourceManifest(
        source_id="bad",
        source_type="dataset",
        origin="user_upload",
        location="../secret.csv",
        trust_level="user_provided",
        intended_use=["test"],
        allowed_operations=["read_files"],
    )
    assert validate_manifest(manifest)


def test_third_party_requires_human_review():
    manifest = ExternalSourceManifest(
        source_id="repo",
        source_type="repo",
        origin="github",
        location="external/inbox/raw/repo",
        trust_level="third_party_open_source",
        intended_use=["reference"],
        allowed_operations=["read_files"],
    )
    assert requires_human_review(manifest)
