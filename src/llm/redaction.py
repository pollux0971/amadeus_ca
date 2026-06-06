"""Secret redaction for LLM request/response logging.

Replaces high-confidence secret patterns with a placeholder. It never returns or
logs the original secret value. These patterns mirror
`scripts/check_secret_hygiene.py` (kept here so this runtime module has no
dependency on the CLI script).
"""
from __future__ import annotations

import re

REDACTED = "***REDACTED***"

# Order matters: more specific prefixes first (sk-ant- before sk-).
_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-proj-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{32,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"(?i)\bauthorization\s*[:=]\s*[A-Za-z0-9._\-]{16,}"),
]


def redact_text(text: str) -> str:
    """Return text with any suspected secret replaced by the placeholder."""
    if not isinstance(text, str):
        return text
    out = text
    for rx in _PATTERNS:
        out = rx.sub(REDACTED, out)
    return out


def redact_mapping(obj):
    """Recursively redact string values in dicts / lists / strings."""
    if isinstance(obj, dict):
        return {k: redact_mapping(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact_mapping(v) for v in obj]
    if isinstance(obj, str):
        return redact_text(obj)
    return obj
