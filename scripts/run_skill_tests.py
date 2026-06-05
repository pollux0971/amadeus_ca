from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.skills_runtime.loader import discover_skills
from src.skills_runtime.validator import validate_skill
from src.skills_runtime.registry import build_registry


def main() -> int:
    skills = discover_skills(ROOT / "skills")
    if not skills:
        print("[FAIL] no skills discovered")
        return 1

    all_ok = True
    for pkg in skills:
        errors = validate_skill(pkg)
        if errors:
            all_ok = False
            print(f"[FAIL] {pkg.skill_id}")
            for error in errors:
                print(f"  - {error}")
            continue

        tests = pkg.manifest.get("tests", {}).get("unit", [])
        for test in tests:
            test_path = pkg.root / test
            proc = subprocess.run([sys.executable, str(test_path)], cwd=str(ROOT), text=True, capture_output=True)
            if proc.returncode != 0:
                all_ok = False
                print(f"[FAIL] {pkg.skill_id}::{test}")
                print(proc.stdout)
                print(proc.stderr)
            else:
                print(f"[PASS] {pkg.skill_id}::{test}")

    registry = build_registry(ROOT / "skills", ROOT / ".cache/skill_registry.json")
    print(f"Generated .cache/skill_registry.json with {len(registry['skills'])} skills")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
