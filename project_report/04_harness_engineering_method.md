# 04 — Harness Engineering Method

The method is the contribution: build the **harness** (the control framework) first,
then add capability through it.

## Principles

1. **Harness-first.** The framework controls context, tools, **trace**,
   **evaluation**, the **safety gate**, and **promotion** around the model — not the
   prompt.
2. **Skills as testable assets.** Each skill has unit tests + evals; behavior is
   proven, not asserted in prose.
3. **CLI + Browser isolation (ADR-003).** Browser/page/file content is **untrusted
   data** and can never become a shell command, tool call, repair, or promotion.
4. **Trace-based evaluation.** Every run records trace + score + artifacts (redacted)
   so failures are debuggable and progress is measurable.
5. **Gated phases + bounded stories.** Capability ships as a gated phase frozen by a
   checkpoint; forward work is one bounded story per run, no auto-extension.
6. **Fail-closed defaults.** Fake provider by default; real APIs need explicit
   operator opt-in; missing key / not-approved → do not call.

## The candidate / promotion lifecycle

```
dev candidate → staging-ready → (human review) → staging → stable
```

Real implementations live as **candidates** under `harnesses/candidates/`; stable
skills are never edited directly. Promotion is gated by
`specs/harness/promotion_policy.md` and a human shell-execution review.

## Self-evolution, but gated

The agent can improve itself, but only along a one-way, human-gated chain that stops
at workspaces:

```
failed eval → repair proposal → approved apply → candidate merge → staging
            (each: redacted, allowlisted, human-approved, workspace-only, no replan)
→ [BLOCKED] stable promotion
```

There is **no autonomous replan** and **no automated path to stable**. Each link
shipped with its own eval at 1.0 and a checkpoint.

## How the method is enforced

- Validators (`validate_workflows` + sub-validators) gate docs, contracts, and
  invariants on every change.
- The secret hygiene scanner blocks any committed secret.
- Redaction (`src/llm/redaction.py`) sanitizes every artifact.
- Per-story tests lock the boundaries of each capability.
