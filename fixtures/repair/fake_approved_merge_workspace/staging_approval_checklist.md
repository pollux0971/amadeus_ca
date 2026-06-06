# Staging approval checklist (must be cleared by a human before any staging promotion)

> STAGING WORKSPACE ONLY — STABLE UNTOUCHED — NOT STABLE PROMOTED

- source merge workspace: `fixtures/repair/fake_approved_merge_workspace`
- merge was candidate-workspace-only: **true**
- merge stable_modified: **false**
- merge promoted: **false**
- merge rollback_available: **true**

This is a FAKE, redacted staging-approval checklist fixture used to exercise the
staging promotion pipeline. It contains no secret.

## Required sign-offs

- [x] A human reviewed the candidate merge workspace's merged changes.
- [x] The rollback plan was reviewed and is sufficient.
- [x] The promotion review package was reviewed.
- [x] No merged change targets a stable skill, the safety gate, or the promotion policy.
- [x] No merged change is a raw shell / direct command / delete.
- [x] Staging lands in a NEW staging workspace, NOT in stable or an active candidate.
- [x] Stable promotion (if any) follows `specs/harness/promotion_policy.md` separately.

## Explicit staging approval

APPROVED_FOR_STAGING_PROMOTION: true
Reviewer: fixture-staging-reviewer

> The marker above plus a named reviewer authorizes promotion into a staging
> **workspace only** — never to stable, never to an active candidate, never a
> stable promotion.
