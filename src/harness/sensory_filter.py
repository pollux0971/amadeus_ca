from __future__ import annotations

import re
from dataclasses import dataclass


PROTECTED_PATTERNS = [
    r"[\w./-]+\.(?:tsx|jsx|py|js|ts|json|yaml|yml|toml|md|html|css)",
    r"localhost:\d+",
    r"127\.0\.0\.1:\d+",
    r"https?://[^\s]+",
    r"line \d+",
    r"exit code \d+",
    r"[A-Z_][A-Z0-9_]{2,}",
    r"\b(?:Error|Exception|Traceback|AssertionError|TypeError|ReferenceError|SyntaxError)\b",
]

NOISY_PREFIXES = (
    "webpack compiled",
    "vite v",
    "npm notice",
    "download progress",
    "[vite] connecting",
    "[vite] connected",
)


@dataclass
class CompressedObservation:
    summary: str
    protected_terms: list[str]
    raw_refs: list[str]
    compression_method: str = "rule_based"
    confidence: float = 0.8

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "protected_terms": self.protected_terms,
            "raw_refs": self.raw_refs,
            "compression_method": self.compression_method,
            "confidence": self.confidence,
        }


def extract_protected_terms(text: str) -> list[str]:
    terms: list[str] = []
    for pattern in PROTECTED_PATTERNS:
        terms.extend(re.findall(pattern, text))
    # Preserve order while removing duplicates.
    seen = set()
    result = []
    for term in terms:
        if isinstance(term, tuple):
            term = "".join(term)
        if term and term not in seen:
            seen.add(term)
            result.append(term)
    return result


def filter_cli_log(text: str, raw_ref: str = "cli.log") -> CompressedObservation:
    lines = text.splitlines()
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if not stripped:
            continue
        if lower.startswith(NOISY_PREFIXES):
            continue
        if any(keyword in lower for keyword in ["error", "failed", "traceback", "exception", "warning", "exit code"]):
            kept.append(stripped)
        elif extract_protected_terms(stripped):
            kept.append(stripped)
    protected = extract_protected_terms("\n".join(kept) or text)
    summary = "\n".join(kept[:20]) if kept else "No critical CLI log lines detected."
    return CompressedObservation(summary=summary, protected_terms=protected, raw_refs=[raw_ref])


def filter_browser_console(text: str, raw_ref: str = "browser_console.log") -> CompressedObservation:
    lines = text.splitlines()
    kept = []
    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in ["error", "exception", "failed", "warning", "source", "line"]):
            kept.append(line.strip())
    protected = extract_protected_terms("\n".join(kept) or text)
    summary = "\n".join(kept[:20]) if kept else "No critical browser console lines detected."
    return CompressedObservation(summary=summary, protected_terms=protected, raw_refs=[raw_ref])
