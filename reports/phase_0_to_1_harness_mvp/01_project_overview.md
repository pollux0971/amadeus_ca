# 01 · Project Overview

## Project name

**Agent Harness Project** — a harness-engineered, self-evolving skill system for
CLI + browser automation.

## One-line summary

Instead of building one clever agent, we build the **harness around** the agent:
a testable, traceable, evolvable control layer where each capability is a
versioned, evaluated *skill candidate* that can be promoted only through gates.

## Problem background

A coding/automation agent that "uses a browser and a terminal" is easy to demo
and hard to trust. Real failures come from the *outside* of the model: what the
agent was allowed to see, what tool it ran, whether the result was verified,
whether a change was safe, and whether you can reproduce and repair it later. A
bare prompt-and-tools agent gives you none of that structure.

## Why not just a browser-use agent

- A browser-use agent optimizes a single run; it has no notion of *which version*
  of a capability ran, whether it passed an eval, or whether it can be rolled
  back.
- Browser/web content is untrusted, and CLI commands carry local risk — these
  must be isolated and gated, not left to the model's discretion.
- "It worked once in the demo" is not the same as "this capability is correct,
  measured, and promotable." We want the latter.

## Why harness engineering

The harness is the external control layer that decides, per step, **what the
agent sees, what it can run, how it is recorded, and how it is evaluated**. It
turns capabilities into *skill packages* (testable assets), records every action
as a trace, scores runs against eval tasks, and routes changes through a
**candidate → eval → promotion** workflow with a safety gate. This makes the
system measurable, reproducible, repairable, and safe to evolve.

## This phase's goal: the 0→1 harness MVP

Stand up the smallest complete version of that loop:

- a **walking skeleton** (eval task → skill registry → skill execution →
  `trace.jsonl` → `score.json`),
- a **thin vertical slice** (fix a real bug, start a server, open a browser, run
  tests) backed by **real candidate skills**,
- a **candidate overlay** mechanism so new versions can be exercised before
  promotion,
- and **gates** (safety, promotion, real-browser) that keep evolution honest.

The goal of 0→1 is *not* "lots of code" — it is "every core module is wired,
measured, and gated."
