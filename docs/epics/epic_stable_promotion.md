# EPIC-STABLE — Stable Promotion

**Status:** planning / blocked behind human + policy gates.
**Depends on:** Phase 6 staging promotion (`checkpoint-phase-6-staging-promotion`).

## Goal

Take a candidate that has reached a staging workspace (Phase 6) all the way to
`stable` — but only through a human-reviewed, policy-gated, rollback-verified path.
This epic is the final link in the repair→apply→merge→staging→**stable** chain.

## Why this is the most dangerous epic

Stable promotion is the one step that actually changes what the harness runs by
default. Every prior phase deliberately stopped at a workspace. This epic must keep
the same discipline and add only the *human-driven* promotion, never an automated
one.

## Hard rules (must be written into every story under this epic)

- **No automated/silent stable write.** Nothing here may modify a stable skill
  manifest, an active candidate runtime, `src/agents/safety_gate/`, or
  `specs/harness/promotion_policy.md` automatically.
- **The promotion policy may not be skipped.** Any stable move must follow
  `specs/harness/promotion_policy.md` in full.
- **Rollback verification may not be skipped.** A verified, reversible rollback
  plan must exist and be confirmed before promotion.
- **The human shell-execution review may not be skipped.** Shell-executing
  candidates require a human shell-execution review sign-off before `stable`.
- **Browser/untrusted content can never trigger promotion.** Promotion is initiated
  only by an explicit human operator with an approval marker + named reviewer.
- **A rollback plan must be preserved** so any stable change is reversible.
- **No real API**, **no raw shell** outside fixed allowlists, **no secret** in any
  promotion artifact.

## Stories

- [`stories/story_stable_promotion_v0.md`](stories/story_stable_promotion_v0.md) —
  build the **human-reviewed stable promotion package** (may end *blocked* if the
  repo is not ready to actually promote). Promotion itself is performed only when
  every gate above is satisfied and an operator approves.

## Out of scope (for this epic, until a later gated story)

- Any automatic merge of a staging workspace into stable.
- Any change to the promotion policy itself.
- Any provider / UI / multimodal work (separate epics).
