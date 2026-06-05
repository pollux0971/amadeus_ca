from pathlib import Path
from src.skills_runtime.loader import discover_skills

def test_discover_skills():
    skills = discover_skills(Path("skills"))
    ids = {s.skill_id for s in skills}
    assert "inspect_project" in ids
    assert "start_local_server" in ids
