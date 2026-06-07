# 05 — Required Human Review (before any GO)

The audit recommends **NO-GO / BLOCKED**. A human (operator + reviewer) must complete
ALL of the following before a future, separately-gated stable-promotion story may even
be attempted. **None of these can be done by automation.**

## Required human gates (all currently unmet)

- [ ] **Human shell-execution review sign-off.** Review the shell-executing
  candidates (`patch_file_and_run_tests_v2`, `start_local_server_v1.2`) and their
  `human_shell_review` material; sign off that the executed commands are safe.
- [ ] **Promotion-policy review sign-off.** Confirm the promotion follows
  `specs/harness/promotion_policy.md` in full (no step skipped).
- [ ] **Deployed-state rollback verification.** Define and verify a rollback that
  reverts a *stable* change (stronger than the workspace-delete rollback used so far);
  a human confirms it works.
- [ ] **Full regression attestation.** Run the regression suite for the intended
  stable cut and record a human-signed attestation of the result.
- [ ] **Explicit operator approval.** Capture an explicit approval marker + named
  reviewer authorizing the stable promotion.

## Process (for the future stable-promotion story — NOT this audit)

1. Clear every checkbox above (human actions, recorded).
2. A separate, gated **stable-promotion story** performs the promotion strictly under
   `specs/harness/promotion_policy.md`, with the captured approval marker and the
   verified rollback in hand.
3. That story must never modify the safety gate or the promotion policy, and must keep
   the verified rollback available.

## Invariants that must still hold during/after promotion

- No real API call; fake provider stays default unless a separate provider gate is
  cleared.
- No raw shell outside vetted scripts; no secret in any artifact.
- Browser/untrusted content can never trigger the promotion.
- A `/goal` run executes one bounded story; promotion is its own bounded story.

> Until every box above is checked by a human, stable promotion stays **blocked** and
> this audit's recommendation stays **NO-GO**.
