from pathlib import Path
import json


def inspect_project(project_dir: str) -> dict:
    path = Path(project_dir)
    if not path.exists():
        return {"status": "failed", "error": "directory_not_found"}

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
        "status": "ok",
        "project_type": project_type,
        "detected_files": sorted(files),
        "start_command": start_command,
        "test_command": test_command,
        "notes": [],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    args = parser.parse_args()
    print(json.dumps(inspect_project(args.project_dir), ensure_ascii=False, indent=2))
