# Branch B Apply Checklist (human, pre-apply)

> ⚠️ **DRAFT.** This checklist gates the manual application of the Branch B
> drafts. **It is not automatically applied.** Every box must be checked, with
> evidence from a real `run_playwright_gate.py` run, before editing the official
> status docs.

## Gate evidence (from the real, non-dry-run gate)

- [ ] `python scripts/run_playwright_gate.py` returned **exit 0** (PASS).
- [ ] eval `open_localhost_playwright_required_smoke` **score = 1.0**.
- [ ] `engine=playwright` in the browser result / score metrics.
- [ ] `is_real_browser=true`.
- [ ] `js_supported=true`.
- [ ] `console_supported=true`.
- [ ] `screenshot_supported=true` **and** a `screenshot.png` artifact exists.
- [ ] a `page_snapshot.json` artifact exists.
- [ ] **no lingering server/browser process** after the run.

## Invariants (must still hold)

- [ ] `stable skills / safety_gate / promotion_policy untouched`.
- [ ] `patch_file_and_run_tests_v2` and `start_local_server_v1.2` unchanged.
- [ ] nothing was installed by the gate (Playwright/Chromium were already present).

## Approval

- [ ] **Operator approval to apply the Branch B docs** (sign-off).

## Apply order (only after every box above is checked)

1. Apply `candidate_status_matrix.patch.md` to `docs/candidate_status_matrix.md`.
2. Apply `promotion_readiness_review.patch.md` to `docs/promotion_readiness_review.md`.
3. Apply `next_milestone_plan.patch.md` to `docs/next_milestone_plan.md`.
4. Apply `quick_resume.patch.md` to `docs/quick_resume.md`.
5. Flip `open_localhost_browser_v1` `candidate.yaml` `status: dev → staging-ready`.
6. Create `docs/checkpoints/phase_1a_playwright_gate_passed.md` with the gate
   evidence.

Do **not** start `read_browser_console` or run the full browser gate as part of
applying Branch B; those are separate, later steps.
