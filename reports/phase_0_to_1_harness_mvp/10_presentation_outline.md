# 10 · Presentation Outline

Suggested deck: **10–14 slides**. Diagrams are in `06_architecture_diagrams.md`;
demo commands are in `05_demo_script.md`.

| # | Slide title | Key points | Visual / demo |
|---|---|---|---|
| 1 | Title | Project name + one-line summary (`01`) | — |
| 2 | Problem | Browser/CLI agents are easy to demo, hard to trust; outside-the-model failures (`01`) | — |
| 3 | Why harness engineering | Control what the agent sees/runs/records/evaluates; capabilities as testable skills (`01`) | — |
| 4 | System architecture | Orchestrator, registry, overlay, skills, safety gate, evaluator, promotion gate (`02`) | *Overall Harness Architecture* (`06`) |
| 5 | Stable vs candidate | Overlay activates the highest active version; all new work is candidates (`02`) | *Candidate Overlay Flow* (`06`) |
| 6 | 0→1 walking skeleton | eval → registry → skill → trace → score (`03`) | **Demo A** |
| 7 | Patch runner evolution | v1 demo-specific → v2 plan-driven reusable (`03`,`04`) | *Patch Runner Flow* (`06`) + **Demo B/C** |
| 8 | Server lifecycle | v1 → keep_alive/teardown → lease reaper (`03`,`04`) | *Server Keep-Alive Handoff* (`06`) + **Demo D** |
| 9 | Browser + the honesty gate | http_fallback smoke 1.0 but **not a real browser**; capability flags (`03`,`08`) | *Browser Gate Flow* (`06`) + **Demo E** |
| 10 | Why blocking is correct | read_browser_console blocked so it isn't built on a fake console (`03`,`08`) | — |
| 11 | Results | 98/98 unit, all e2e/demo 1.0, gates scaffolded, no lingering, invariants kept (`07`) | results table (`07`) |
| 12 | Risks & limitations | not a real browser, advisory lease, no LLM planner, no autonomy yet (`08`) | — |
| 13 | Next phase | Playwright gate → console skill → full e2e → planner/UI; gates not to skip (`09`) | *Promotion Gate Flow* (`06`) |
| 14 | Closing / checkpoint | tag `checkpoint-0-to-1-harness-gates`; how to resume (`12`) | — |

**Demo order in the talk:** A → B → C → D → E, then show the two gate `--dry-run`
outputs to explain what is intentionally blocked.

If trimming to 10 slides: merge 4+5, merge 7+8, drop 14 (mention the tag on 13).
