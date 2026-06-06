"""Failure analyzer — read a failed run's artifacts and classify the failure.

Reads ONLY redactable run artifacts (`score.json`, `summary.md`, `trace.jsonl`).
It never reads `.env`, a password file, or any secret, and it redacts every text
it keeps. Output is a `FailureAnalysis` with a coarse `failure_type`.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.llm.redaction import redact_text
from src.repair.types import FailureAnalysis, FailureSignal

# Artifacts we are allowed to read. Anything else (and especially secrets) is off
# limits — the analyzer only ever opens these names.
_ALLOWED_ARTIFACTS = ("score.json", "summary.md", "trace.jsonl")


def _classify(unmet: list[str], signals: list[FailureSignal]) -> str:
    """Map the observed signals to a coarse failure_type."""
    text = " ".join([*unmet, *[s.kind + " " + s.detail for s in signals]]).lower()
    if any(k in text for k in ("screenshot", "artifact", "_ref", "snapshot", "missing_artifact")):
        return "missing_artifact"
    if any(k in text for k in ("fatal", "console_error", "pageerror", "console")):
        return "console_error"
    if any(k in text for k in ("test", "tests_pass", "test_failed")):
        return "test_failed"
    if any(k in text for k in ("runtime", "playwright", "browser_runtime", "not_implemented")):
        return "runtime_missing"
    if unmet:
        return "criterion_failed"
    return "unknown"


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def analyze_failure(source: str | Path) -> FailureAnalysis:
    """Analyze a failed run.

    `source` may be a run directory (containing score.json/summary.md/trace.jsonl)
    or a path to a single failure report (summary.md / failure_report.md). Only the
    allowed artifacts are read; everything kept is redacted.
    """
    src = Path(source)
    run_dir = src if src.is_dir() else src.parent
    run_ref = redact_text(str(run_dir))

    signals: list[FailureSignal] = []
    unmet: list[str] = []
    summary_text = ""

    # --- score.json: unmet criteria + failure block -----------------------
    score_path = run_dir / "score.json"
    if score_path.exists():
        score = _read_json(score_path)
        for r in score.get("criteria_results", []):
            if not r.get("passed", True):
                crit = str(r.get("criterion", ""))
                unmet.append(crit)
                signals.append(FailureSignal(
                    source="score", kind="criterion_failed",
                    detail=redact_text(str(r.get("note", ""))), criterion=crit))
        failure = score.get("failure") or {}
        if failure.get("root_cause"):
            signals.append(FailureSignal(
                source="score", kind="root_cause",
                detail=redact_text(str(failure.get("root_cause")))))

    # --- summary.md: redacted text (metadata only) ------------------------
    report_path = src if (src.is_file() and src.name in _ALLOWED_ARTIFACTS or
                          (src.is_file() and src.name.endswith(".md"))) else run_dir / "summary.md"
    if report_path.exists() and report_path.is_file():
        raw = report_path.read_text(encoding="utf-8")
        summary_text = redact_text(raw)[:4000]  # cap; redacted
        low = raw.lower()
        if "fail" in low:
            signals.append(FailureSignal(source="summary", kind="summary_fail",
                                         detail="summary reports a failure"))

    # --- trace.jsonl: METADATA only (step success flags, error types) -----
    trace_path = run_dir / "trace.jsonl"
    if trace_path.exists():
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev_out = ev.get("output", {}) or {}
            err = (ev_out.get("error") or {}) if isinstance(ev_out, dict) else {}
            if err and err.get("type"):
                signals.append(FailureSignal(
                    source="trace", kind="step_error",
                    detail=redact_text(str(err.get("type")))))
            ev_eval = ev.get("evaluation", {}) or {}
            if ev_eval.get("step_success") is False:
                skill = (ev.get("actor", {}) or {}).get("skill_id", "")
                signals.append(FailureSignal(
                    source="trace", kind="step_failed",
                    detail=redact_text(str(skill))))

    failure_type = _classify(unmet, signals)
    return FailureAnalysis(
        run_ref=run_ref,
        failure_type=failure_type,
        unmet_criteria=unmet,
        signals=signals,
        summary=summary_text,
        metadata={"artifacts_read": [a for a in _ALLOWED_ARTIFACTS
                                     if (run_dir / a).exists()]},
    )
