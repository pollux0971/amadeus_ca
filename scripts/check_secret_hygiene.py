"""Secret hygiene checker.

Conservative checks that NEVER print secret values:
  - required .gitignore rules are present,
  - no secret-like file is git-tracked,
  - tracked files contain no high-confidence API-key pattern.

It only ever outputs FILE NAMES + a RISK LABEL — never the matched value. Exit
code 2 if a secret file is tracked or a key pattern is found in a tracked file;
exit 1 if only .gitignore rules are missing; 0 if clean.

It scans only `git ls-files` (tracked, in-repo) — so out-of-repo secret files are
never read or scanned.
"""
from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_GITIGNORE = [
    ".env", ".env.*", "*.env", "password_and_api.txt",
    "secrets/", ".secrets/", "*.key", "*.pem",
]

# File names git should never track (the template .env.example is exempt).
TRACKED_SECRET_GLOBS = [
    "*.env", ".env", "password*.txt", "passwords*", "*.pem", "*.key",
    "*.p12", "*.pfx", "id_rsa", "id_ed25519", "*.token", "secrets.*",
    "*credentials*.json", "*credentials*.txt",
]

# High-confidence, provider-prefixed key patterns. Names are reported; values are
# never printed. (These regex literals do not match themselves.)
KEY_PATTERNS = {
    "openai_key": re.compile(r"sk-[A-Za-z0-9]{32,}"),
    "openai_project_key": re.compile(r"sk-proj-[A-Za-z0-9_\-]{20,}"),
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    "aws_access_key_id": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "github_fine_grained_pat": re.compile(r"github_pat_[A-Za-z0-9_]{40,}"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
}

# Files allowed to *mention* key patterns (policy/spec/scanner/tests/template).
SCAN_ALLOWLIST = {
    "scripts/check_secret_hygiene.py",
    "tests/unit/test_secret_hygiene.py",
    "docs/secrets_policy.md",
    "specs/llm/llm_provider_contract.md",
    ".env.example",
}


def _git_tracked(root: Path) -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=str(root), capture_output=True,
                             text=True, check=True).stdout
    except Exception:  # noqa: BLE001
        return []
    return [line for line in out.splitlines() if line]


def missing_gitignore_rules(root: Path) -> list[str]:
    gi = root / ".gitignore"
    lines = set()
    if gi.exists():
        lines = {ln.strip() for ln in gi.read_text(encoding="utf-8").splitlines()}
    missing = [r for r in REQUIRED_GITIGNORE if r not in lines]
    if "runs/" not in lines and "runs/*" not in lines:
        missing.append("runs/")
    return missing


def tracked_secret_files(root: Path) -> list[str]:
    hits = []
    for f in _git_tracked(root):
        name = Path(f).name
        if name == ".env.example":
            continue
        if any(fnmatch.fnmatch(name, g) for g in TRACKED_SECRET_GLOBS):
            hits.append(f)
    return hits


def scan_tracked_for_keys(root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for f in _git_tracked(root):
        if f in SCAN_ALLOWLIST:
            continue
        try:
            text = (root / f).read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        for risk, rx in KEY_PATTERNS.items():
            if rx.search(text):
                findings.append((f, risk))  # NB: value intentionally not stored
    return findings


def check(root: Path) -> dict:
    return {
        "missing_gitignore": missing_gitignore_rules(root),
        "tracked_secret_files": tracked_secret_files(root),
        "key_findings": scan_tracked_for_keys(root),
    }


def main() -> int:
    result = check(ROOT)

    if result["missing_gitignore"]:
        print("[WARN] .gitignore is missing rules: " + ", ".join(result["missing_gitignore"]))
    else:
        print("[OK] .gitignore covers the required secret rules")

    if result["tracked_secret_files"]:
        print("[FAIL] secret-like files are git-tracked (REMOVE from git):")
        for f in result["tracked_secret_files"]:
            print(f"  - {f}")
    else:
        print("[OK] no secret-like file is git-tracked")

    if result["key_findings"]:
        print("[FAIL] possible API-key pattern in tracked files (value NOT shown):")
        for f, risk in result["key_findings"]:
            print(f"  - {f}: {risk}")
    else:
        print("[OK] no API-key pattern found in tracked files")

    if result["tracked_secret_files"] or result["key_findings"]:
        return 2
    if result["missing_gitignore"]:
        return 1
    print("[PASS] secret hygiene OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
