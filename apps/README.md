# Apps

Application surfaces live here. Keep UI and user-facing applications separate from the core harness.

Current planned app:

- `web_console/`: a future read-only dashboard for runs, skills, eval reports, and external source intake.

Rules:

1. Apps call harness APIs instead of directly mutating core files.
2. Apps can create candidate changes, but promotion still follows `specs/harness/promotion_policy.md`.
3. Apps must have their own tests and API contract.
