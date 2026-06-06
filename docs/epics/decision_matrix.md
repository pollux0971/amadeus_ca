# Decision Matrix — choosing the next story

Pick **one** bounded story for the next `/goal` run. Compare the four candidate
epics on value, risk, dependencies, required gates, and reasons to choose now vs
defer. **A `/goal` run executes exactly one bounded story** and must not
auto-extend into another.

## Comparison

| Option | Value | Risk | Dependencies | Required gates | Reason to choose now | Reason to defer |
|---|---|---|---|---|---|---|
| **Stable Promotion** ([story](stories/story_stable_promotion_v0.md)) | High — completes the repair→stable chain | **Highest** — only step that changes what runs by default | Phase 6 staging (`checkpoint-phase-6-staging-promotion`) | human review, verified rollback, full regression, human shell-execution review, promotion policy, operator approval | The chain is otherwise complete; a packaged human review is the natural next artifact | Actual promotion needs human sign-off + may be **blocked** until the repo is truly ready |
| **UI Dashboard** ([story](stories/story_ui_dashboard_v0.md)) | Medium — visibility into phases/gates/runs | Low (planning only) | read-only over existing artifacts | read-only, redacted, no promote-from-UI, actions via existing scripts | Cheap, safe, improves operator situational awareness | No new runtime capability; pure planning until a build story |
| **Real Provider** ([story](stories/story_real_provider_v0.md)) | Medium/High — real reasoning eventually | **High** — network egress + key handling = secret-leak risk | `src/llm/` fake provider + config contract | no real API, env-var-name only, redaction, operator opt-in, fail closed | Unblocks future real planning once the threat model is written | Real calls cost money + risk; fake provider already exercises the interface |
| **Multimodal / Data Channels** ([story](stories/story_multimodal_channel_v0.md)) | Medium — new input surfaces | **High** — new untrusted-content surface | CLI+Browser isolation (ADR-003), redaction | source isolation, untrusted≠instruction, per-channel eval, redaction | Expands what the harness can ingest | Each channel needs its own eval + isolation review first |

## Recommendation guidance

- **Lowest-risk, highest-clarity next step:** `story_ui_dashboard_v0` or
  `story_real_provider_v0` (both planning-only, no runtime change).
- **Highest-value but gated:** `story_stable_promotion_v0` — only proceed if a human
  is ready to clear the promotion gates; otherwise it produces the review package
  and is marked **blocked**.
- Whatever is chosen: **one bounded story**, then checkpoint/report and stop.

> This matrix is a decision aid, not an authorization. Choosing an option still
> requires its story's preconditions and gates to be satisfied.
