# 11 — Conclusion

This project demonstrates a **harness-engineered** browser-use / computer agent: a
system that does real work — drives a real browser, patches and tests code, and even
evolves its own skills — while keeping the blast radius **bounded and auditable**.

The contribution is the **gated harness**, not a single agent:

- Capability ships as **gated, testable phases** (1B → 6), each frozen by a checkpoint
  and proven by an eval at 1.0.
- The agent can **propose and stage its own fixes** through a one-way, human-gated
  chain (repair → apply → merge → staging) that stops at workspaces.
- The last line — **stable promotion** — is deliberately **blocked**; a formal audit
  recommends **NO-GO / BLOCKED** until human gates are cleared.
- Defaults are safe: **fake provider** (no real API), **read-only dashboard**, **no
  secret committed**, **untrusted content can never trigger an action**.

Measured results: unit tests **453/453**; vite demo **1.0**; real-browser e2e **1.0**;
dashboard read-only smoke **1.0**; the full repair/planner eval chain **1.0** — all
with **stable skills / safety_gate / promotion_policy untouched** and **no real API**.

The takeaway: with harness engineering, an agent's *capability* and its *safety* grow
together — every new power arrives behind a gate, a test, and (for the dangerous
steps) a human. The remaining frontier (stable promotion, real provider, multimodal,
action UI) is mapped as bounded, gated stories, so the system can keep advancing
without ever becoming an unbounded autonomous agent.
