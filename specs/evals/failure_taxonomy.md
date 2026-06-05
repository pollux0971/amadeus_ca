# Failure Taxonomy

## Skill Failures

- manifest_invalid
- missing_required_file
- unit_test_failed
- entrypoint_failed
- precondition_missing
- postcondition_failed
- output_schema_mismatch

## CLI Failures

- command_blocked
- command_timeout
- command_not_found
- missing_dependency
- test_failed
- permission_denied
- unsafe_command_detected

## Browser Failures

- page_load_timeout
- element_not_found
- console_error_detected
- navigation_failed
- browser_crashed
- prompt_injection_detected

## Orchestration Failures

- wrong_agent_selected
- wrong_skill_selected
- context_missing_goal
- repeated_loop
- premature_final_answer
- plan_drift

## Safety Failures

- secret_access_attempt
- secret_leak
- browser_to_cli_injection
- destructive_command_attempt
- unapproved_network_access

## Evaluation Failures

- criteria_not_verifiable
- fixture_not_resettable
- flaky_task
- score_inconsistent
