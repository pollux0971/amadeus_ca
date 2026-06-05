from pathlib import Path
import tempfile
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

def inspect_project(path: Path) -> dict:
    files = {p.name for p in path.iterdir()}
    if "package.json" in files:
        project_type = "node"
        start_command = "npm run dev"
        test_command = "npm test"
    elif "pyproject.toml" in files or "requirements.txt" in files:
        project_type = "python"
        start_command = None
        test_command = "pytest"
    else:
        project_type = "unknown"
        start_command = None
        test_command = None
    return {
        "project_type": project_type,
        "detected_files": sorted(files),
        "start_command": start_command,
        "test_command": test_command,
    }

def test_node_project():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "package.json").write_text("{}")
        result = inspect_project(p)
        assert result["project_type"] == "node"
        assert result["start_command"] == "npm run dev"

def test_python_project():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "pyproject.toml").write_text("[project]\nname='x'")
        result = inspect_project(p)
        assert result["project_type"] == "python"
        assert result["test_command"] == "pytest"

if __name__ == "__main__":
    test_node_project()
    test_python_project()
