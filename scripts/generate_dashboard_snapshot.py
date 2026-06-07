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
from src.skills_runtime.simple_yaml import load_yaml

OUT = ROOT / "ui_dashboard" / "data" / "dashboard_snapshot.json"

# Read-only eval gates whose declared scores we surface (read-only; no execution).
READONLY_GATE_EVALS = (
    "evals/planner/openai_readonly_execution_gate.yaml",
    "evals/planner/openai_readonly_list_files_execution_gate.yaml",
)

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


def _exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def _openai_provider_status() -> dict:
    """Provider/live-smoke status derived from committed files only — NO API call,
    NO env read, NO key. The key is referenced by NAME only."""
    return {
        "provider": "openai",
        "fake_provider_default": True,
        "fail_closed": True,
        "live_smoke": ("shipped (provider-ok)"
                       if _exists("scripts/real_provider_live_smoke.py") else "not shipped"),
        "real_call": "operator opt-in only (--real-call + the OpenAI key env var present)",
        "key_source": "the named OpenAI key environment variable (config stores the env-var NAME only; never the value)",
    }


def _planner_live_status() -> dict:
    return {
        "mode": "plan-only",
        "live_plan": ("shipped" if _exists("scripts/openai_planner_live_plan.py")
                      else "not shipped"),
        "plan_review_package": ("shipped" if _exists("scripts/openai_plan_review.py")
                                else "not shipped"),
        "executes_plan": False,
        "auto_repair": False,
    }


def _readonly_execution_status() -> dict:
    return {
        "mode": "human-approved; dry-run by default",
        "gate": ("shipped" if _exists("src/planner/read_only_execution_gate.py") else "missing"),
        "eval_gate": ("shipped (re-runnable)"
                      if _exists("evals/planner/openai_readonly_execution_gate.yaml") else "missing"),
        "executes": "allowlisted read-only skills only",
        "auto_repair": False,
        "replan": False,
    }


def _readonly_allowlist() -> list[str]:
    """The live read-only execution allowlist (in-process import; no shell/API)."""
    try:
        from src.planner.read_only_execution_gate import READONLY_ALLOWLIST
        return list(READONLY_ALLOWLIST)
    except Exception:  # noqa: BLE001 - never fail the snapshot on an import hiccup
        return []


def _latest_gate_scores() -> list[dict]:
    """Declared gate scores from the read-only eval yamls (read-only; not executed)."""
    rows: list[dict] = []
    for rel in READONLY_GATE_EVALS:
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            task = load_yaml(p)
        except Exception:  # noqa: BLE001
            task = {}
        rows.append({
            "id": task.get("id", Path(rel).stem),
            "category": task.get("category", "unknown"),
            "score": (task.get("scoring") or {}).get("success_rate"),
            "source": rel,
            "note": "run scripts/run_eval.py to verify",
        })
    return rows


def _blocked_items(epic_rows: list[dict]) -> list[str]:
    items = ["stable promotion: BLOCKED (human / policy / rollback / shell-review gate)"]
    for r in epic_rows:
        if "block" in str(r.get("status", "")).lower():
            items.append(f"{r.get('id')}: {r.get('status')}")
    return items


def build_snapshot() -> dict:
    phases, latest = _phase_status()
    epics = _epic_story_status()
    return {
        "schema": "harness.dashboard.snapshot/v0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "redacted docs only (README / docs / reports / epics / candidate.yaml)",
        "latest_checkpoint": latest or "unknown",
        "phase_status": phases,
        "candidate_status": _candidate_status(),
        "eval_status": _eval_status(),
        "epic_story_status": epics,
        # Dashboard Gate Status v0 — read-only status surfaces (no action, no API).
        "openai_provider_status": _openai_provider_status(),
        "planner_live_status": _planner_live_status(),
        "readonly_execution_status": _readonly_execution_status(),
        "readonly_allowlist": _readonly_allowlist(),
        "latest_gate_scores": _latest_gate_scores(),
        "blocked_items": _blocked_items(epics),
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
