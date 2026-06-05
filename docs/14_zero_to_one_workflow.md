# 0→1 Workflow — 從零建立第一個可跑 Agent Harness

本文件定義「從零開始」時應該怎麼開發。它的目標不是一次做完所有功能，而是建立一條能被測試、能被記錄、能被擴充的最小垂直切片。

---

## 1. 0→1 的定義

0→1 指的是：

```text
從空 repo / 初始骨架
→ 建立第一個可以跑的 harness
→ 完成第一個 CLI + Browser demo
→ 產生 trace、score、report
```

0→1 不包含：

```text
完整 UI
完整 multi-modal pipeline
任意網站自動操作
完整 Claude Code / Codex 自動修復
learned multi-agent topology
大規模 skill graph 自動演化
```

這些都屬於 1→N 或後續研究。

---

## 2. 0→1 的核心原則

### 2.1 Harness first

先做 harness，不先做超大 agent。

```text
先有：schema、runner、trace、eval、安全規則
再有：LLM decision、multi-agent、auto repair
```

原因：如果沒有 harness，agent 的成功和失敗都無法被測試，也無法被改進。

### 2.2 Thin vertical slice

Keyword: thin vertical slice

不要橫向做一堆半成品。

錯誤做法：

```text
CLI agent 寫一半
Browser agent 寫一半
UI 寫一半
memory 寫一半
```

正確做法：

```text
做一條非常窄但完整的流程：
讀 task → 選 skill → 執行 → 記錄 trace → 評分 → 產生 report
```

### 2.3 每個模組先能被測試

每個核心模組都要先有 unit test 或 smoke test：

```text
skills_runtime/loader.py
skills_runtime/validator.py
harness/trace_logger.py
harness/evaluator.py
agents/safety_gate
agents/cli_agent
agents/browser_agent
```

---

## 3. 0→1 階段總覽

```text
M0. Repo Skeleton
M1. Skill Package Runner
M2. Trace Logger
M3. CLI Agent + Safety Gate
M4. Browser Agent
M5. Orchestrator
M6. Verifier + Scorer
M7. CLI + Browser Demo
M8. Minimal Report Generator
```

---

## 4. M0 — Repo Skeleton

Before this milestone, the project has no walking skeleton. The goal of M0-M2 is to create a walking skeleton that passes through task loading, skill registry, trace logging, and scoring.

### 目標

建立專案結構與最基本測試環境。

### 要建立的目錄

```text
docs/
specs/
src/
skills/
evals/
fixtures/
runs/
scripts/
tests/
```

### 必要文件

```text
README.md
START_HERE.md
FILE_INDEX.md
docs/00_project_brief.md
docs/01_problem_definition.md
docs/02_system_overview.md
docs/03_glossary.md
```

### 完成條件

```bash
pytest -q
python scripts/validate_structure.py
python scripts/validate_workflows.py
```

都必須 pass。

---

## 5. M1 — Skill Package Runner

### 目標

讓系統能讀取、驗證、列出 skill packages。

### 最小功能

```text
1. 讀取 skills/*/manifest.yaml
2. 檢查 SKILL.md / gene.yaml / manifest.yaml 是否存在
3. 建立 registry
4. 顯示 skill id、version、risk_level、permissions
```

### 必要檔案

```text
src/skills_runtime/loader.py
src/skills_runtime/validator.py
src/skills_runtime/registry.py
scripts/run_skill_tests.py
specs/skills/skill_package_spec.md
```

### 第一個 skill

```text
skills/inspect_project/
```

用途：讀取專案目錄，判斷 Python / Node / Vite / unknown。

### 完成條件

```bash
python scripts/run_skill_tests.py
```

輸出應包含：

```text
[PASS] inspect_project
Generated .cache/skill_registry.json
```

---

## 6. M2 — Trace Logger

### 目標

每次執行都能產生可追蹤資料。

### 最小 trace 結構

```text
runs/<run_id>/
├── task.yaml
├── trace.jsonl
├── artifacts/
├── score.json
└── summary.md
```

### 每個 trace event 至少包含

```yaml
run_id: string
step_id: string
agent_id: string | null
skill_id: string | null
action_type: string
input_ref: string | null
output_summary: string
artifact_refs: list
success: bool
error: string | null
```

### 完成條件

跑任何 demo 都能在 `runs/` 看到 trace。

---

## 7. M3 — CLI Agent + Safety Gate

### 目標

讓 harness 能安全地執行本地命令。

### CLI Agent 可以做

```text
讀取專案檔案
列出目錄
執行 pytest
執行 npm script
啟動本地 server
收集 stdout/stderr
```

### CLI Agent 不可以做

```text
rm -rf
sudo
cat .env
curl | bash
上傳本地檔案到外部網站
執行未審核 install script
```

### 必要檢查

```text
command allowlist
denylist
working directory boundary
timeout
stdout/stderr capture
secret pattern scanner
```

### 完成條件

```text
pytest 可以跑
npm run dev 可以跑
危險命令會被阻擋並記錄在 trace
```

---

## 8. M4 — Browser Agent

### 目標

讓 harness 可以打開 localhost 頁面、讀取 console、擷取基本 DOM 狀態。

### Browser Agent 最小功能

```text
open_url(url)
read_title()
extract_visible_text_summary()
list_interactable_elements()
read_console_errors()
save_screenshot()
```

### 第一階段只支援

```text
localhost
fixture HTML
本地 Vite/React app
```

先不要支援任意網站登入、購物、金流、社群網站操作。

### 完成條件

```text
能打開 fixtures/browser_prompt_injection_page/index.html
能擷取 console error
能產生 screenshot artifact ref
```

---

## 9. M5 — Orchestrator

### 目標

把 task、skill、agent、trace 串起來。

### 第一版不要太聰明

0→1 階段可以用 rule-based orchestrator。

```text
如果 task 需要 inspect project → CLI Agent
如果 task 需要 start server → CLI Agent
如果 task 需要 open localhost → Browser Agent
如果 task 需要 verify → Verifier Agent
```

### Orchestrator 必須維護

```yaml
user_goal: string
current_subgoal: string
completed_steps: list
remaining_steps: list
artifacts: list
pinned_evidence: list
risk_level: low | medium | high
```

### 完成條件

能讀取：

```text
evals/cli_browser_integration/vite_login_bug.yaml
```

並依序執行最小流程。

---

## 10. M6 — Verifier + Scorer

### 目標

不要讓 agent 自己說成功就算成功。

### Verifier 檢查

```text
success_criteria 是否完成
forbidden_actions 是否出現
required_artifacts 是否存在
tests 是否通過
browser console 是否還有 fatal error
budget 是否超過
```

### score.json 應包含

```yaml
task_success: bool
criteria_results: map
forbidden_action_results: map
step_count: int
tool_call_count: int
runtime_sec: float
context_tokens_estimated: int
budget_violation_count: int
failure_reason: string | null
```

---

## 11. M7 — CLI + Browser Demo

### 目標

完成第一個可展示 vertical slice。

### Demo 任務

```text
fixture: fixtures/vite_login_bug
任務: 修復 login page runtime error
```

### 執行流程

```text
1. InspectProject
2. StartLocalServer
3. OpenLocalhostBrowser
4. ReadBrowserConsole
5. PatchFileAndRunTests
6. VerifyBrowserState
7. GenerateReport
```

### 完成條件

```text
dev server started
browser opened localhost
console error collected
source file patched
tests pass
browser fatal error resolved
trace.jsonl exists
score.json exists
summary.md exists
```

---

## 12. M8 — Minimal Report Generator

### 目標

讓 demo 可以被老師、同學、自己快速理解。

### report 應包含

```text
任務目標
執行步驟
使用 skills
CLI commands
Browser actions
關鍵 evidence
修復前/後差異
score
budget 使用量
失敗或風險
```

---

## 13. 0→1 完成檢查清單

```text
[ ] repo skeleton complete
[ ] validate_structure pass
[ ] validate_workflows pass
[ ] pytest pass
[ ] 5 core skills exist
[ ] skill registry generated
[ ] trace logger works
[ ] CLI command runner exists
[ ] safety gate blocks dangerous commands
[ ] browser agent can open localhost
[ ] evaluator produces score.json
[ ] vite_login_bug demo runs
[ ] report generator produces summary.md
```

---

## 14. 0→1 不該做的事

不要在 0→1 階段做：

```text
完整前端 dashboard
真正自動改 production code
自動學習 topology
真實網站購物/登入
完整多模態模型推理
大規模資料庫整合
雲端部署
```

這些都等 1→N 工作流處理。

---

## 15. 0→1 的最短實作順序

```text
1. validate_structure.py
2. skill loader / validator / registry
3. inspect_project skill
4. trace_logger
5. safety_gate
6. CLI command runner
7. start_local_server skill
8. browser controller
9. open_localhost_browser skill
10. read_browser_console skill
11. evaluator / scorer
12. run_demo.py
13. vite_login_bug fixture
14. report generator
```

---

## 16. 0→1 的設計底線

如果某個模組還不能實作，允許 placeholder；但 placeholder 必須滿足：

```text
有明確 TODO
有 input/output contract
有測試或 skip reason
不假裝已完成
不進 stable demo path
```

