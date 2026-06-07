# 12 — Presentation Script (5–8 minutes)

A spoken-word script for presenting the project. Times are guidance; total ≈ 5–8 min.
Brackets `[...]` are stage directions / commands to show.

---

**[0:00–0:45] Opening / problem.**
"Browser and computer agents are powerful — they can drive a browser, run shell
commands, and change code. But that power is dangerous: an unchecked agent can leak
secrets, follow malicious web content, or silently change production. My project asks
a different question: not *how clever can the agent be*, but *how do we keep it
bounded and auditable while it does real work?*"

**[0:45–1:30] System goal.**
"The answer is **harness engineering**. Instead of trusting a prompt, I built the
**harness** — the framework that controls context, tools, traces, evaluation, the
safety gate, and promotion. Every capability is a **gated, testable phase**, and
defaults are safe: a **fake LLM provider** with no real API, a **read-only
dashboard**, and **stable promotion blocked**."

**[1:30–2:30] Method.**
"Skills are testable assets with their own evals. Browser content is treated as
untrusted data — it can never become a command. Each phase is frozen by a checkpoint
and proven by an eval at 1.0. [Show: `python scripts/validate_workflows.py` — all
gates green.]"

**[2:30–3:30] Browser end-to-end demo.**
"Here's a real vertical slice: the system starts a server, opens it in a real browser,
reads the console, patches the bug, re-opens, and confirms it's fixed. [Show: `python
scripts/run_demo.py --demo vite_login_bug` → 1.0.] The full real-browser e2e (Phase
1B) runs in Playwright and also scores 1.0."

**[3:30–4:45] Self-evolution chain — gated.**
"The interesting part: the system can fix *itself*. A failed eval becomes a **repair
proposal**, then an **approved apply** into a workspace, then a **candidate merge**,
then a **staging** promotion — each step human-approved, redacted, and workspace-only,
with a rollback plan. Crucially, there is **no autonomous path to stable**. It
proposes and stages, but a human must promote."

**[4:45–5:45] Dashboard + safety.**
"A **read-only dashboard** visualizes status from a redacted snapshot — no buttons, no
actions, no secrets, no external network. [Show: `python scripts/run_dashboard_smoke.py
--dry-run`; note the real smoke is 1.0.] The hard boundaries — no real API, no
`password_and_api.txt`, no raw shell, no stable/safety/promotion modification, no
browser-content-triggered actions — are enforced by validators, a secret scanner, and
per-story tests, not by good intentions."

**[5:45–6:45] Results + the audit.**
"Numbers: unit tests 453/453; demo, real-browser e2e, dashboard smoke, and the whole
repair chain all at 1.0. And the honest part: I ran a **stable promotion readiness
audit** — its recommendation is **NO-GO / BLOCKED**, because the human review gates
aren't met. That's the system working as intended: it refuses to cross the last line
without a human."

**[6:45–8:00] Future work + close.**
"Future work is mapped as bounded, gated stories: human-reviewed stable promotion, an
action UI behind new gates, a real provider with operator opt-in, and multimodal
channels with per-channel isolation evals. The takeaway: with harness engineering, an
agent's capability and its safety grow together — every new power arrives behind a
gate, a test, and, for the dangerous steps, a human. Thank you."

---

## Q&A backup points

- *Why fake provider?* Reproducible, free, safe in CI; real providers are a separate
  gated story (operator opt-in, redaction tests, fail closed).
- *Has the system promoted anything to stable?* No — the audit is **NO-GO /
  BLOCKED**; that's deliberate.
- *Can the browser content hijack the agent?* No — CLI + Browser isolation; untrusted
  content is data, never an instruction.
