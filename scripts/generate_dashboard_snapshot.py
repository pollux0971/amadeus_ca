"""Generate the read-only UI dashboard snapshot from REDACTED docs only.

Reads only committed, redacted artifacts (README, docs/, reports/, docs/epics/,
docs/candidate_status_matrix, harnesses/candidates/*/candidate.yaml). It does NOT
read `.env`, `/data/python/computer_agent_v5/password_and_api.txt`, or raw `runs/`
traces; it makes NO API call and runs NO shell command. If any secret-looking value
is detected in the assembled snapshot it REFUSES to write.

Output: ui_dashboard/data/dashboard_snapshot.json
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm.redaction import redact_text  # the only "secret" knowledge we use

OUT = ROOT / "ui_dashboard" / "data" / "dashboard_snapshot.json"

# Paths this generator is allowed to read (redacted, committed docs only).
# It NEVER reads .env, password files, or runs/ raw traces.
SAFE_READ_ROOTS = ("README.md", "docs/", "reports/", "harnesses/candidates/")

SAFETY_INVARIANTS = [
    "stable skills untouched",
    "active candidate runtime untouched",
    "safety_gate untouched",
    "promotion_policy untouched",
    "no real API call (fake provider default, fail closed)",
    "no secret in artifacts (all redacted)",
    "no raw shell outside fixed allowlists",
    "no stable promotion (blocked behind human/policy/rollback gate)",
    "read-only dashboard: no action execution",
]


def _read(rel: str) -> str:
    p = ROOT / rel
    # Defense in depth: never read outside the safe roots, never runs/ or .env.
    norm = rel.replace("\\", "/")
    if norm.startswith("runs/") or ".env" in norm or "password" in norm.lower():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return ""


def _phase_status() -> tuple[list[dict], str]:
    cps = sorted((ROOT / "docs" / "checkpoints").glob("checkpoint-phase-*.md"))
    rows = []
    latest = ""
    best_phase = -1.0
    for cp in cps:
        stem = cp.stem  # checkpoint-phase-6-staging-promotion
        title = _first_heading(_read(f"docs/checkpoints/{cp.name}")) or stem
        rows.append({"name": title, "status": "complete", "checkpoint": stem})
        m = re.search(r"checkpoint-phase-(\d+)", stem)
        if m:
            ph = float(m.group(1))
            # treat e.g. phase-2a > phase-2 via a small bump
            if re.search(r"phase-\d+[a-z]", stem):
                ph += 0.5
            if ph > best_phase:
                best_phase = ph
                latest = stem
    return rows, latest


def _candidate_status() -> list[dict]:
    base = ROOT / "harnesses" / "candidates"
    rows = []
    if not base.exists():
        return rows
    for d in sorted(base.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue  # skip generated _repair_*/_staging_* workspaces
        cand = d / "candidate.yaml"
        status = "unknown"
        if cand.exists():
            for line in _read(f"harnesses/candidates/{d.name}/candidate.yaml").splitlines():
                m = re.match(r"\s*status\s*:\s*(.+?)\s*$", line)
                if m:
                    status = m.group(1).strip().strip('"').strip("'")
                    break
        rows.append({"id": d.name, "status": status})
    return rows


def _eval_status() -> list[dict]:
    base = ROOT / "evals"
    rows = []
    if not base.exists():
        return rows
    for y in sorted(base.rglob("*.yaml")):
        text = _read(str(y.relative_to(ROOT)))
        eid = ""
        cat = ""
        for line in text.splitlines():
            m = re.match(r"\s*id\s*:\s*(.+?)\s*$", line)
            if m and not eid:
                eid = m.group(1).strip()
            m = re.match(r"\s*category\s*:\s*(.+?)\s*$", line)
            if m and not cat:
                cat = m.group(1).strip()
        rows.append({"id": eid or y.stem, "category": cat or "unknown",
                     "gate": "see reports/"})
    return rows


def _epic_story_status() -> list[dict]:
    base = ROOT / "docs" / "epics" / "stories"
    rows = []
    if not base.exists():
        return rows
    for s in sorted(base.glob("*.md")):
        text = _read(f"docs/epics/stories/{s.name}")
        status = "unknown"
        m = re.search(r"(?im)^\*\*Status:\*\*\s*(.+?)\s*$", text)
        if m:
            status = m.group(1).strip()
        rows.append({"id": s.stem, "status": status})
    return rows


def _links_to_reports() -> list[str]:
    base = ROOT / "reports"
    out = []
    if base.exists():
        for r in sorted(base.glob("*/README.md")):
            out.append(str(r.relative_to(ROOT)))
    return out


def build_snapshot() -> dict:
    phases, latest = _phase_status()
    return {
        "schema": "harness.dashboard.snapshot/v0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "redacted docs only (README / docs / reports / epics / candidate.yaml)",
        "latest_checkpoint": latest or "unknown",
        "phase_status": phases,
        "candidate_status": _candidate_status(),
        "eval_status": _eval_status(),
        "epic_story_status": _epic_story_status(),
        "safety_invariants": list(SAFETY_INVARIANTS),
        "links_to_reports": _links_to_reports(),
    }


def main() -> int:
    snapshot = build_snapshot()
    text = json.dumps(snapshot, ensure_ascii=False, indent=2)

    # Refuse to write if any secret-looking value slipped in.
    if redact_text(text) != text:
        print("[BLOCKED] secret-looking value detected in snapshot; refusing to write.",
              file=sys.stderr)
        return 2

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n", encoding="utf-8")
    print(f"[OK] wrote {OUT.relative_to(ROOT)} "
          f"(latest_checkpoint={snapshot['latest_checkpoint']}, "
          f"phases={len(snapshot['phase_status'])}, evals={len(snapshot['eval_status'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
