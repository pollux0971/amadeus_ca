# Phase Report — 0→1 Harness MVP

This folder is the **stage report pack** for the first phase of the project. It
collects the results so far into report-ready material: overview, architecture,
workflow, candidate evolution, demo script, diagrams, evaluation results, risks,
and the next-phase plan. Everything here is documentation — no runtime code.

- **Corresponds to checkpoint tag:** `checkpoint-0-to-1-harness-gates`
  (see `../../docs/checkpoints/checkpoint-0-to-1-harness-gates.md`).

## Completed in this phase

- 0→1 **walking skeleton** end to end (eval → registry → candidate overlay →
  skill → `trace.jsonl` → `score.json`).
- Real candidate skills with a candidate overlay resolver:
  - `patch_file_and_run_tests_v2` — plan-driven reusable patch runner (staging-ready
    after human shell review; v1 superseded).
  - `start_local_server_v1.2` — subprocess server lifecycle + keep_alive +
    teardown + lease reaper.
  - `open_localhost_browser_v1` — consumes the kept-alive server; **HTTP fallback
    smoke = 1.0** (not a real browser yet).
- Safety + promotion discipline preserved; gate runners scaffolded.
- All smoke/e2e/demo at 1.0; `run_unit_tests` 98/98.

## Not done / blocked (by design)

- **open_localhost_browser_v1** stays `dev` — **http_fallback is not a real
  browser**; needs the Playwright gate.
- **read_browser_console is blocked** — must wait for a real browser.
- **Playwright real-browser gate** and **full browser e2e gate** are scaffolded
  but **not executed** (no Playwright/Chromium here).

## Next phase entry

Run the Playwright real-browser gate in a Playwright + Chromium environment
(`python scripts/run_playwright_gate.py`), then proceed per
`09_next_phase_plan.md`.

## Contents

| File | Purpose |
|---|---|
| `01_project_overview.md` | what the project is and why |
| `02_system_architecture.md` | components and how they fit |
| `03_workflow_zero_to_one.md` | the 0→1 workflow + candidate evolution |
| `04_candidate_evolution_summary.md` | per-candidate stage / result / risk |
| `05_demo_script.md` | demos A–E: commands, expected output, narration |
| `06_architecture_diagrams.md` | Mermaid diagrams |
| `07_evaluation_results.md` | current results |
| `08_risks_and_limitations.md` | risks and honest limitations |
| `09_next_phase_plan.md` | ordered next steps + gates not to skip |
| `10_presentation_outline.md` | slide outline (10–14 slides) |
| `11_teacher_explanation.md` | plain-language explanation |
| `12_artifact_index.md` | index of the key files |
