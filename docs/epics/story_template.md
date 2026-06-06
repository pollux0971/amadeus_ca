# Story Template

Copy this file to `stories/story_<name>_v<n>.md` for a new bounded story. A `/goal`
run executes **exactly one** story and must not auto-extend into another.

---

# Story <ID> — <Title>

**Epic:** <EPIC-ID>
**Status:** ready | blocked | in progress | done

## Goal

One sentence: the user/operator value this story delivers.

## Scope

What this story *does* (bounded). Bullet the concrete deliverables.

## Out of Scope

What this story explicitly does **not** do (defer to a future story).

## Preconditions

What must already be true to start (prior checkpoint, an approval marker, a green
gate). If a precondition is unmet, the story is **blocked** — record it and stop.

## Implementation Boundaries

Where work may touch (e.g. `docs/`, `tests/`, a new workspace dir) and where it may
**not** (stable skills, `safety_gate`, `promotion_policy`, active candidate runtime).

## Acceptance Criteria

Checklist of objectively verifiable outcomes. The story is done only when all hold.

## Forbidden Zone

Hard "never" list for this story (no real API, no stable modification, no raw
shell, no secret, no untrusted-content-as-instruction, etc.).

## Required Validation Commands

The exact commands that must pass (e.g. `python scripts/validate_workflows.py`,
`python scripts/run_unit_tests.py`). Fixed allowlist only — never derived input.

## Artifacts to Produce

The files / workspace / report this story creates (all redacted; no secret).

## Rollback / Stop Condition

How to undo this story's effect, and the explicit **Stop Condition**: when to stop
(Definition of Done met, or a precondition/gate fails → mark blocked and stop). No
cross-story continuation.

## Definition of Done

The precise end state: acceptance criteria met, validation green, a checkpoint or
report update written, working tree clean, and **stop**.
