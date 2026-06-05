# 08 · Risks and Limitations

Honest list of what is *not* solid yet. Several of these are **deliberate gates**,
not unfinished work.

## Browser realism

- **http_fallback is not a real browser.** `open_localhost_browser_v1` currently
  loads pages with a pure-HTTP fallback (`urllib` + `html.parser`): no JavaScript
  execution, no rendered DOM, no console, no screenshot. A client-rendered SPA
  would snapshot as near-empty. Every result is labeled `engine=http_fallback`,
  `is_real_browser=false` so a passing score is never mistaken for a real browser.
- **Playwright / Chromium environment is not yet verified.** The real-browser path
  is wired (used automatically once Playwright is installed) but has **not** been
  executed here. The Playwright gate exists but is unrun.

## Blocked-by-design

- **read_browser_console is blocked.** It must depend on `browser_mode=playwright`;
  a console built on the HTTP fallback would be fake/empty and would corrupt
  downstream evaluations (ADR-013). Blocking it is the correct design, not a gap.

## Robustness gaps

- **The lease reaper is not an OS-level watchdog.** It mitigates crash-residual
  kept-alive servers (session registry + `reap_sessions`), but the lease is
  advisory: between a crash and the next reaper run a stale server can survive up
  to `lease_ttl_sec`. A hard guarantee would need a cgroup/systemd-scope or a
  supervised reaper.

## Promotion / safety

- **Shell execution needs human review.** `patch_file_and_run_tests_v2` and
  `start_local_server_v1.2` run shell commands through the Safety Gate; per the
  promotion policy they need a human shell-execution sign-off before `stable`.
- **patch_v2 still needs human review before stable.** It is staging-ready, not
  stable.

## Scope of this phase

- **No LLM planner.** The orchestrator is rule-based; step selection is fixed, not
  model-driven.
- **No real multi-agent autonomy.** "Agents" here are skill executors under a
  deterministic harness; there is no autonomous agent negotiation or open-ended
  planning yet.
- The Safety Gate is a **denylist**, not an allowlist; trusted operator-authored
  commands (eval/plan/inspect) can pass. Untrusted/browser content never reaches
  command construction by design.
