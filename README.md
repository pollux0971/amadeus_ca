# Agent Harness Project

本專案是一套 **基於 Harness Engineering 的 CLI + Browser 多代理技能測試與自動演化系統**。

它的目標不是只做一個會用 browser 或 CLI 的 agent，而是建立一個可測試、可記錄、可修復、可逐步演化的 agent harness。  
系統會把能力封裝成 skill package，透過 trace logging、benchmark evaluation、failure report、candidate patch、promotion policy 來讓 Claude Code / Codex 類 coding agent 協助更新技能與 harness。

---

## Quick Start

### 1. 檢查專案結構與工作流

```bash
python scripts/validate_structure.py
python scripts/validate_workflows.py
```

### 2. 驗證所有 skill package

```bash
python scripts/run_skill_tests.py
```

### 3. 執行示範 demo

```bash
python scripts/run_demo.py --demo vite_login_bug
```

目前 demo runner 是可擴充骨架，會讀取 eval task、建立 run folder、寫入 trace 與 score。  
實際 browser automation 可在 `src/agents/browser_agent/` 補上 Playwright 或 browser-use 實作。

---

## Current Harness Candidate Status

Index only — see the linked docs for detail. **One-minute resume:**
[`docs/quick_resume.md`](docs/quick_resume.md). **Latest checkpoint:**
[`docs/checkpoints/checkpoint-phase-1b-full-browser-e2e.md`](docs/checkpoints/checkpoint-phase-1b-full-browser-e2e.md)
— **the full real-browser e2e (`full_browser_vite_login_bug_e2e`) is now green
(1.0)**. (Earlier: [`checkpoint-0-to-1-harness-gates.md`](docs/checkpoints/checkpoint-0-to-1-harness-gates.md).)

- Full matrix: [`docs/candidate_status_matrix.md`](docs/candidate_status_matrix.md)
- Promotion verdicts: [`docs/promotion_readiness_review.md`](docs/promotion_readiness_review.md)
- Ordered next steps: [`docs/next_milestone_plan.md`](docs/next_milestone_plan.md)
- Playwright real-browser gate eval: [`evals/browser/open_localhost_playwright_required_smoke.yaml`](evals/browser/open_localhost_playwright_required_smoke.yaml)
- Full real-browser e2e (draft): [`evals/browser/full_browser_vite_login_bug_e2e.yaml`](evals/browser/full_browser_vite_login_bug_e2e.yaml)
- Playwright gate runner: [`scripts/run_playwright_gate.py`](scripts/run_playwright_gate.py)
- Full-browser gate runner: [`scripts/run_full_browser_gate.py`](scripts/run_full_browser_gate.py)

**Must-know flags (do not lose these):**

- **full_browser_vite_login_bug_e2e is GREEN (1.0)** — the full real-browser chain
  (start → open → console → patch → re-open → re-console) passes via
  `scripts/run_full_browser_gate.py` in a Playwright env (`engine=playwright`,
  `is_real_browser=true`). See `checkpoint-phase-1b-full-browser-e2e`.
- **http_fallback is not a real browser** — without Playwright the browser/console
  steps degrade to a non-browser smoke (`engine=http_fallback`,
  `is_real_browser=false`); the real gates require the Playwright engine.
- **open_localhost_browser_v1 is staging-ready** (Playwright gate passed);
  **read_browser_console_v1 is `dev`, real-browser only** (rejects http_fallback).
- **Real-browser gates/evals run via the project `.venv`** (Playwright + Chromium
  installed there). `--dry-run` on the gate runners is always safe anywhere.
- **stable skills / safety_gate / promotion_policy are untouched**; `stable`
  promotion still needs a human shell-execution + policy review.

## Gate Chain

The promotion path, in order (each step gates the next):

```text
patch_file_and_run_tests_v2            (staging-ready, after human shell review)
  → start_local_server_v1.2            (dev/staging-candidate: keep_alive + teardown + lease reaper)
  → open_localhost_browser_v1          (dev: http_fallback smoke = 1.0; NOT a real browser)
  → Playwright real-browser gate       (scripts/run_playwright_gate.py — not yet run)
  → read_browser_console_v1            (BLOCKED until a real browser exists; must force browser_mode=playwright)
  → full_browser_vite_login_bug_e2e    (DRAFT / BLOCKED until the two steps above)
```

Safe to run anywhere (no browser launched, nothing installed):

```bash
python scripts/run_playwright_gate.py --dry-run
python scripts/run_full_browser_gate.py --dry-run
```

---

## Phase Reports

Stage report packs (overview, architecture, demos, diagrams, results, risks,
next-phase plan) — ready to use for write-ups and slides:

- [`reports/phase_0_to_1_harness_mvp/README.md`](reports/phase_0_to_1_harness_mvp/README.md)
  — 0→1 Harness MVP (checkpoint `checkpoint-0-to-1-harness-gates`).

---

## Core Ideas

- **Harness-first architecture**：重點不是 prompt，而是控制 context、tool、trace、evaluation 的外部框架。
- **Skill package lifecycle**：skill 是可測試資產，不是單純 markdown。
- **CLI + Browser isolation**：Browser 內容視為不可信，CLI 具有本機風險，兩者必須隔離。
- **Trace-based evaluation**：每次執行都保存 trace、score、artifacts，讓後續修復有依據。
- **Claude Code / Codex assisted repair**：coding agent 根據 failure report 修改 candidate，再由測試與 promotion policy 決定是否升級。
- **Efficiency-first evaluation**：成功率之外，也追蹤 steps、tool calls、runtime、context tokens、cost-of-success。
- **Budgeted planning and tool use**：Planning、CLI、Browser、retry 都受明確 budget 控制。
- **Brownfield + extension workflow**：新 UI、資料渠道、多模態功能、外部開源專案都先進入 `external/`，再經過 manifest、adapter、eval、promotion gate。

---

## Repository Map

```text
docs/       人類閱讀的設計文件
specs/      開發者與 coding agent 必須遵守的系統規格
src/        核心程式骨架
skills/     可測試技能包
evals/      benchmark 任務定義
fixtures/   demo 與測試用專案
runs/       每次執行產生的 trace、score、report
scripts/    開發與測試入口
tests/      系統級測試
external/   外部資料、開源專案、多模態素材的固定 intake 區
apps/       未來全端介面或其他使用者介面
```

---

## Recommended Reading Order

0. `START_HERE.md`
1. `WORKFLOW_INDEX.md`
2. `docs/14_zero_to_one_workflow.md`
3. `docs/15_one_to_n_workflow.md`
4. `docs/00_project_brief.md`
2. `docs/01_problem_definition.md`
3. `docs/02_system_overview.md`
4. `specs/harness/harness_contract.md`
8. `specs/skills/skill_package_spec.md`
9. `specs/harness/trace_schema.md`
10. `docs/05_demo_plan.md`
11. `docs/09_efficiency_agent_survey_notes.md`
12. `docs/10_conflict_and_staleness_review.md`
13. `specs/harness/efficiency_metrics.md`
14. `docs/11_brownfield_harness_workflow.md`
15. `specs/brownfield/brownfield_workflow.md`
16. `specs/extensions/extension_adapter_spec.md`

---

## Current MVP Targets

- MVP-0：Skill Package Runner
- MVP-1：CLI Agent Harness
- MVP-2：Browser Agent Harness
- MVP-3：CLI + Browser Integration Demo
- MVP-4：Auto Skill Repair Loop
- MVP-5：Context Router / Multi-turn Robustness Demo

詳細內容見 `docs/05_demo_plan.md`。


## Brownfield Extension Quick Rule

未來要加入新功能時，不要直接改核心 agent。先把資料、開源專案或原型放進 `external/inbox/raw/`，補上 manifest，再用 adapter、eval、promotion policy 進入系統。全端介面放在 `apps/`，多模態與資料渠道輸出 `ArtifactRef`，不要把原始檔案直接塞進 prompt。


## Workflow Split

- **0→1**：從零開始建立第一個可跑 harness，請看 `docs/14_zero_to_one_workflow.md`。
- **1→N**：在穩定 harness 上新增 UI、資料渠道、多模態或外部專案，請看 `docs/15_one_to_n_workflow.md`。

每次開始實作前先跑：

```bash
python scripts/validate_structure.py
python scripts/validate_workflows.py
pytest -q
```
