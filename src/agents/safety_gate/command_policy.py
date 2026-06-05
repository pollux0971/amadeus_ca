from __future__ import annotations

import re


DENY_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bcat\s+\.env\b",
    r"\bcat\s+~\/\.ssh\b",
    r"\bcurl\b.*\|\s*bash",
    r"\bwget\b.*\|\s*bash",
    r"\bformat\b",
]


def check_command(command: str) -> tuple[bool, str | None]:
    normalized = command.strip()
    for pattern in DENY_PATTERNS:
        if re.search(pattern, normalized):
            return False, f"blocked by deny pattern: {pattern}"
    return True, None
