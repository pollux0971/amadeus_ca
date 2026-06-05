from __future__ import annotations

from pathlib import Path
from .loader import SkillPackage


REQUIRED_FILES = ["SKILL.md", "manifest.yaml", "gene.yaml"]


def validate_skill(pkg: SkillPackage) -> list[str]:
    errors: list[str] = []

    for filename in REQUIRED_FILES:
        if not (pkg.root / filename).exists():
            errors.append(f"missing required file: {filename}")

    manifest = pkg.manifest
    if manifest.get("id") != pkg.skill_id:
        errors.append(f"manifest id {manifest.get('id')!r} does not match folder {pkg.skill_id!r}")

    for key in ["version", "level", "domain", "risk_level", "tests"]:
        if key not in manifest:
            errors.append(f"manifest missing key: {key}")

    if manifest.get("risk_level") not in {"low", "medium", "high"}:
        errors.append("risk_level must be low, medium, or high")

    tests = manifest.get("tests", {})
    unit_tests = []
    if isinstance(tests, dict):
        unit_tests = tests.get("unit", []) or []
    if not unit_tests:
        errors.append("no unit tests declared")

    for test_path in unit_tests:
        if not (pkg.root / test_path).exists():
            errors.append(f"declared test does not exist: {test_path}")

    return errors
