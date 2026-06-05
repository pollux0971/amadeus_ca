# Gherkin Style Guide

Use Gherkin for acceptance criteria, not low-level unit tests.

## Template

```gherkin
Feature: Short feature name

  Scenario: Main success path
    Given initial condition
    And additional context
    When actor performs action
    Then expected result should happen
    And evidence should exist
```

## Example

```gherkin
Feature: Start local web app and verify browser state

  Scenario: Agent starts a Vite project and verifies it in browser
    Given a Vite project exists in "fixtures/vite_login_bug"
    And the project has a known login page bug
    When the CLI agent runs the StartLocalServer skill
    And the Browser agent opens the detected localhost URL
    And the Browser agent reads the console error
    Then the system should map the error to a source file
    And the CLI agent should patch the source file
    And the test runner should pass
    And the Browser agent should verify that no fatal console error remains
```
