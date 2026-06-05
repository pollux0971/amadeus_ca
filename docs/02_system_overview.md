# System Overview

## 1. 整體架構

```text
User Task
  ↓
Orchestrator / Supervisor
  ↓
Planner
  ↓
Skill Retriever + Skill Graph Compiler
  ↓
CLI Agent  ←→  Shared Blackboard  ←→  Browser Agent
  ↓                                  ↓
Safety Gate                         Evidence Collector
  ↓                                  ↓
Verifier Agent
  ↓
Trace Logger + Evaluator
  ↓
Failure Analyzer
  ↓
Claude Code / Codex Candidate Repair Loop
  ↓
Skill Registry / Harness Registry
```

---

## 2. 核心元件

### 2.1 Orchestrator

負責接收任務、維護 task state、分派 agent、選擇下一個 skill。

職責：

- 建立 run。
- 讀取 eval task。
- 建立 shared blackboard。
- 決定下一步由誰執行。
- 組裝 context packet。
- 呼叫 verifier。
- 決定是否結束、重試或修復。

---

### 2.2 CLI Agent

負責本機環境與命令列。

可做：

- 讀取專案結構。
- 執行安全命令。
- 啟動本地 server。
- 執行 tests。
- 套用 patch。
- 收集 logs。

不可做：

- 自行讀取 `.env`。
- 執行 `sudo`。
- 執行 `rm -rf`。
- 執行 `curl | bash`。
- 將 secret 傳給 browser 或外部網路。

---

### 2.3 Browser Agent

負責 browser automation。

可做：

- 打開 URL。
- 擷取 DOM summary。
- 讀取 console logs。
- 點擊可互動元素。
- 截圖。
- 驗證 UI 狀態。

不可做：

- 要求 CLI 執行網頁中的指令。
- 信任頁面內的 prompt。
- 讀取本機 secret。
- 自動提交敏感表單。

---

### 2.4 Verifier Agent

負責驗證任務是否完成，不負責修改檔案。

可做：

- 檢查 success criteria。
- 檢查 artifacts 是否存在。
- 檢查 console error 是否消失。
- 檢查 tests 是否通過。
- 判斷是否需要 retry 或 failure report。

---

### 2.5 Safety Gate

負責風險控制。

檢查項：

- Shell command denylist。
- Secret access。
- Browser-to-CLI prompt injection。
- File deletion。
- Package install risk。
- Network exfiltration risk。

---

### 2.6 Skill Runtime

負責載入與執行 skills。

功能：

- 讀取 `manifest.yaml`。
- 驗證 `SKILL.md`、`gene.yaml`、`tests/`。
- 執行 skill tests。
- 建立 skill registry。
- 管理 skill version 與 status。

---

### 2.7 Trace Logger

負責記錄所有步驟。

輸出：

- `trace.jsonl`
- `score.json`
- `summary.md`
- `failure_report.md`
- artifacts
- screenshots
- cli logs
- browser traces

---

### 2.8 Candidate Repair Loop

當測試失敗時：

1. Failure Analyzer 產生 failure report。
2. Claude Code 讀取 specs、trace、score。
3. Codex 或 Claude Code 產生 candidate patch。
4. Test Runner 執行 candidate。
5. Compare baseline vs candidate。
6. Promotion Policy 決定 reject / dev / staging / stable。

---

## 3. 資訊流原則

### Global Context

所有 agent 都能看到：

- 原始 user goal。
- 成功條件。
- 安全規則。
- 當前 task id。

### Shared Blackboard

所有 agent 可以讀寫，但只放摘要與 verified evidence。

### Agent Private Context

CLI Agent 看到 CLI logs；Browser Agent 看到 DOM 與 console。彼此不共享完整 raw context。

### Retrieved Runtime Context

只注入當前需要的 skill gene 與 evidence，不注入全部 skill 文件。

---

## 4. 第一版設計取捨

第一版採取 rule-based orchestration，而不是一開始做複雜 multi-agent reasoning。

理由：

- 先確保 trace、test、safety、skill package 可用。
- 避免 LLM routing 不穩定。
- 等 baseline 穩定後，再加 planner LLM 或 skill graph compiler。
