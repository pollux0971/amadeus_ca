from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .simple_yaml import load_yaml


@dataclass
class SkillPackage:
    root: Path
    skill_id: str
    manifest: dict

    @property
    def skill_md(self) -> Path:
        return self.root / "SKILL.md"

    @property
    def gene_yaml(self) -> Path:
        return self.root / "gene.yaml"


def discover_skills(skills_dir: str | Path = "skills") -> list[SkillPackage]:
    skills_path = Path(skills_dir)
    packages: list[SkillPackage] = []
    if not skills_path.exists():
        return packages

    for child in sorted(skills_path.iterdir()):
        if not child.is_dir():
            continue
        manifest_path = child / "manifest.yaml"
        if not manifest_path.exists():
            continue
        manifest = load_yaml(manifest_path)
        packages.append(SkillPackage(root=child, skill_id=child.name, manifest=manifest))
    return packages
