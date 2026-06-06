# UI Dashboard — Future Eval List (planning only)

Planning only — **no eval implemented now**. These are the evals to add **when** a
read-only dashboard is eventually built, so its safety properties are gated the same
way as every other capability. Each would be a normal `evals/` task with
`success_criteria`, run via `scripts/run_eval.py`.

## Proposed future evals

| Eval (future) | Goal | Key success criteria |
|---|---|---|
| `ui_read_only_no_action` | The dashboard executes nothing | `no_shell_spawned`, `no_script_invoked`, `no_write_to_repo` |
| `ui_redaction_enforced` | Every rendered string is redacted | `all_rendered_redacted` (redact_text(x)==x), `no_secret_in_render` |
| `ui_no_promotion_path` | UI cannot promote/apply/merge/stage | `no_promote_endpoint`, `actions_route_through_gated_scripts_only` |
| `ui_trace_metadata_only` | Only trace metadata is exposed | `no_raw_trace_payload`, `metadata_fields_only` |
| `ui_reads_allowed_roots_only` | Reads stay within allowed artifact roots | `no_read_outside_runs_reports_docs_evals_candidates` |

## Notes

- These evals do not exist yet and must not be created by this planning story —
  they are the **acceptance bar for a future build story**.
- A build story may only proceed once these evals exist and pass, mirroring how the
  repair→staging chain each shipped with its own eval at 1.0.
- No eval here triggers a real browser, a real API, or any action; they assert the
  *absence* of dangerous behavior (read-only, redacted, no execution).
