from __future__ import annotations

from pathlib import Path
from .loader import discover_skills
from .validator import validate_skill
from .simple_yaml import dump_json


def build_registry(skills_dir: str | Path = "skills", output_path: str | Path = ".cache/skill_registry.json") -> dict:
    registry = {"skills": [], "errors": {}}

    for pkg in discover_skills(skills_dir):
        errors = validate_skill(pkg)
        status = "valid" if not errors else "invalid"
        registry["skills"].append({
            "id": pkg.skill_id,
            "version": pkg.manifest.get("version"),
            "level": pkg.manifest.get("level"),
            "domain": pkg.manifest.get("domain"),
            "risk_level": pkg.manifest.get("risk_level"),
            "status": status,
        })
        if errors:
            registry["errors"][pkg.skill_id] = errors

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(registry, output_path)
    return registry
