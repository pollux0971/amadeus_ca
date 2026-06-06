"""Repair proposal validation — structural + safety checks over a proposal.

The validator NEVER applies a proposal. It rejects proposals that are structurally
broken, that target protected paths (stable skills, safety gate, promotion policy,
secrets), that use a forbidden / shell-style action, that smuggle a secret, that
require but lack approval, or that claim to be already applied.
"""
from __future__ import annotations

import json

from src.llm.redaction import redact_text
from src.repair.types import RepairProposal, RepairValidationResult, RISK_LEVELS

# Allowed declarative action types.
ACTION_ALLOWLIST = (
    "update_candidate", "add_test", "update_docs", "update_eval", "noop",
)

# Forbidden action types — never permitted at this layer.
ACTION_DENYLIST = (
    "modify_stable_skill", "modify_safety_gate", "modify_promotion_policy",
    "raw_shell", "direct_command", "delete_file", "eval", "exec", "bash",
)

# A target path must start with one of these roots.
ALLOWED_TARGET_ROOTS = (
    "harnesses/candidates/", "tests/", "evals/", "docs/", "reports/",
)

# A target path must NOT touch any of these (protected surfaces / secrets).
FORBIDDEN_TARGET_PREFIXES = (
    "skills/", "src/agents/safety_gate/", "specs/harness/promotion_policy.md",
    ".env", "config/config.json",
)


def _contains_secret(text: str) -> bool:
    return redact_text(text) != text


def _target_allowed(target: str) -> bool:
    t = (target or "").lstrip("./")
    if any(t == p or t.startswith(p) for p in FORBIDDEN_TARGET_PREFIXES):
        return False
    return any(t.startswith(root) for root in ALLOWED_TARGET_ROOTS)


def validate_proposal(proposal: RepairProposal) -> RepairValidationResult:
    errors: list[str] = []
    notes: list[str] = []

    if not isinstance(proposal, RepairProposal):
        return RepairValidationResult(valid=False, errors=["not_a_proposal"])

    if not proposal.id:
        errors.append("proposal has no id")

    # A proposal must NEVER claim to be applied at this layer.
    if proposal.applied:
        errors.append("proposal_marked_applied (proposal-only layer forbids applied=true)")

    if not proposal.actions:
        notes.append("proposal has no actions")

    ids: list[str] = []
    for idx, a in enumerate(proposal.actions):
        where = f"action[{idx}] id={a.id!r}"
        if not a.id:
            errors.append(f"{where}: empty action id")
        elif a.id in ids:
            errors.append(f"{where}: duplicate action id {a.id!r}")
        ids.append(a.id)

        at = str(a.action_type)
        if at in ACTION_DENYLIST:
            errors.append(f"{where}: forbidden action_type {at!r}")
        elif at not in ACTION_ALLOWLIST:
            errors.append(f"{where}: action_type {at!r} not in allowlist")

        if not _target_allowed(a.target):
            errors.append(f"{where}: target {a.target!r} outside allowed roots / protected")

        if a.risk_level not in RISK_LEVELS:
            errors.append(f"{where}: illegal risk_level {a.risk_level!r}")
        if a.risk_level == "high" and not a.requires_approval:
            errors.append(f"{where}: high risk action must set requires_approval=true")

    # Secret-looking content anywhere in the proposal → fail closed (no echo).
    try:
        blob = json.dumps(proposal.to_dict(), ensure_ascii=False, default=str)
    except Exception:  # noqa: BLE001
        blob = str(proposal.to_dict())
    if _contains_secret(blob):
        errors.append("proposal contains a secret-looking value")

    return RepairValidationResult(valid=not errors, errors=errors, notes=notes)
