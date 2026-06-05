# 11 · Plain-Language Explanation (for the teacher)

## What is this project, really?

We are building the **scaffolding around** an AI agent that automates a computer
(running terminal commands and opening web pages), rather than building one
"smart agent." The scaffolding — we call it the **harness** — decides what the
agent is allowed to see, what it is allowed to run, records everything it does,
and grades each run against a defined task. Every capability is packaged as a
small, testable **skill**, and new versions of a skill must pass tests and gates
before they're trusted.

## Why do harness engineering instead of "just an agent"?

Because a demo that "works once" is not the same as a system you can trust,
measure, and improve. With a bare agent you can't say *which version* of a
capability ran, whether it passed a test, whether it was safe, or how to
reproduce and fix a failure. The harness gives us all of that: versioned skills,
a recorded trace of every action, an automatic score, a safety gate on shell
commands, and a promotion process. It's the difference between a magic trick and
an engineering process.

## How is this different from a normal agent?

- A normal agent: prompt + tools, optimize one run.
- Our system: a control layer that **gates and grades** the agent's actions, with
  capabilities as testable, versioned assets that evolve through
  candidate → evaluation → promotion.

## What have we completed?

- The full minimal loop ("walking skeleton"): read a task → pick a skill → run it
  → record a trace → produce a score.
- Real working capabilities (as candidates): a **reusable code-patching** skill
  that fixes a bug and runs its tests, a **local web server** skill that starts a
  server, keeps it alive for the next step, and cleans it up afterwards, and a
  **page-loading** skill that opens a local web page.
- A safety gate on shell commands, and a promotion process — both untouched and
  respected the whole time.
- Everything is tested: 98/98 unit tests pass and all the demos score 1.0.

## Why are some features "blocked" — isn't that unfinished?

No — some blocks are **correct design decisions**:

- The page-loading skill currently uses a simple HTTP fetch because this machine
  has no real browser (Playwright) installed. We **label that honestly**: it is a
  "localhost smoke check," not a real browser (no JavaScript, no console).
- The "read the browser console" skill is **deliberately blocked** until a real
  browser exists, because building it on the fake fetch would produce a *fake
  console* and quietly corrupt every later result. Refusing to build it on a fake
  foundation is the responsible choice.

So "blocked" here means "we put a gate here on purpose," not "we ran out of time."

## How do we move forward?

On a machine with a real browser installed, we run a one-command **gate**. If it
passes (proving a real browser really works), only then do we build the console
skill and the full end-to-end test. After that, we can add smarter planning and a
self-repair loop. The order is fixed and the gates are not skipped — that's the
whole point of the harness.
