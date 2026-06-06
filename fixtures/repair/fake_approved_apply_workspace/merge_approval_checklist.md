# Merge approval checklist (must be cleared by a human before any candidate merge)

> CANDIDATE WORKSPACE MERGE ONLY — STABLE UNTOUCHED — NOT PROMOTED

- source apply workspace: `fixtures/repair/fake_approved_apply_workspace`
- apply was workspace-only: **true**
- apply promoted: **false**
- apply stable_modified: **false**

This is a FAKE, redacted merge-approval checklist fixture used to exercise the
candidate merge pipeline. It contains no secret.

## Required sign-offs

- [x] A human reviewed the apply workspace's proposed changes.
- [x] No proposed change targets a stable skill, the safety gate, or the promotion policy.
- [x] No proposed change is a raw shell / direct command / delete.
- [x] The merge will land in a NEW candidate merge workspace, NOT in stable or an active candidate.
- [x] A rollback plan will be produced.
- [x] Promotion (if any) follows `specs/harness/promotion_policy.md` separately.

## Explicit merge approval

APPROVED_FOR_CANDIDATE_MERGE: true
Reviewer: fixture-merge-reviewer

> The marker above plus a named reviewer authorizes merge into a candidate merge
> **workspace only** — never to stable, never to an active candidate, never a
> promotion.
