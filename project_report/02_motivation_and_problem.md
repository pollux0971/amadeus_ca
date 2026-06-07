# 02 — Motivation and Problem

## Motivation

Browser-use / computer agents can do real work — drive a browser, run CLI commands,
patch and test code, even evolve their own skills. But the same power makes them
dangerous: an unchecked agent could run arbitrary shell commands, leak secrets,
follow malicious page content, or silently change what runs in production.

## The problem

The hard problem is **not the prompt** — it is **control**. How do you let an agent
do genuinely useful, real-world work while keeping the **blast radius bounded and
auditable**?

Specifically:

- How do you add capability **incrementally** with a test/eval gate at every step?
- How do you let the agent **propose and stage its own fixes** without letting it
  modify stable code or promote itself?
- How do you treat **browser/file content as untrusted** so it can never become an
  instruction, a tool call, a repair, or a promotion?
- How do you guarantee **no secret** leaks and **no real API** is called unless an
  operator explicitly opts in?

## Approach (this project)

A **harness-first** design: the framework controls context, tools, traces,
evaluation, the safety gate, and promotion around the model. Capabilities ship as
**gated phases** frozen by checkpoints; forward work is organized as **bounded
stories**. The provider is **fake by default** and **fail-closed**; the dashboard is
**read-only**; stable promotion is **blocked** behind human + policy + rollback +
shell-execution review.

## Non-goals

- Not an unbounded autonomous agent.
- Not a real-LLM product (real providers are planning-gated, operator opt-in).
- Not a self-promoting system (no auto path to stable).
