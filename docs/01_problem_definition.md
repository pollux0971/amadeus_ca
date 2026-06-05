# Problem Definition

## 1. 問題背景

LLM agent 逐漸可以使用工具、控制瀏覽器、執行命令列、修改程式碼。然而在實際使用時，單純把工具接到 ReAct loop 並不夠。當任務變長、工具變多、環境觀察變複雜時，agent 會變得不穩定。

本專題將問題聚焦在：

> 如何透過 Harness Engineering 設計一個可測試、可記錄、可修復、可演化的 CLI + Browser 多代理系統？

---

## 2. Pain Points

### P1. 長任務規劃漂移

Agent 在多步任務中容易忘記最初目的。例如原本任務是「修復登入頁並用 browser 驗證」，但 agent 可能只修了程式碼，忘了回到 browser 驗證。

### P2. Context 過載

CLI log、browser DOM、console error、檔案內容、測試輸出都很長。如果全部塞進 prompt，會造成注意力分散與錯誤判斷。

### P3. Skills 不可靠

傳統 skill 常是 markdown 或 prompt。沒有 tests、沒有成功條件、沒有 failure mode、沒有版本管理，因此不適合作為長期能力資產。

### P4. CLI 和 Browser 安全風險不同

Browser 內容通常來自外部或網頁，不能信任。CLI 可以接觸本機檔案、API key、SSH key、.env、系統命令，因此必須隔離。

### P5. 失敗難以追蹤

沒有 trace schema 時，agent 失敗後只能人工看對話。這無法讓 Claude Code / Codex 系統化修復問題。

### P6. 自動更新缺乏驗收流程

Coding agent 可以產生 patch，但如果沒有 baseline comparison、security tests、promotion policy，就可能讓系統越改越壞。

---

## 3. 專題解法

本專題提出一個 harness-first 架構，將能力拆成：

- Orchestrator
- CLI Agent
- Browser Agent
- Verifier Agent
- Safety Gate
- Skill Package Runtime
- Trace Logger
- Evaluator
- Failure Analyzer
- Candidate Repair Loop

其中 harness 負責控制：

- context construction
- skill selection
- agent routing
- tool permissions
- trace logging
- scoring
- promotion

---

## 4. Research Questions

### RQ1

Harness engineering 是否能提升 CLI + Browser agent 在長任務中的穩定性？

### RQ2

將 skills 設計成可測試 package 是否能提升技能可靠性與可重用性？

### RQ3

Trace-based failure report 是否能幫助 Claude Code / Codex 更有效修復 skill 或 harness？

### RQ4

Context isolation 與 Safety Gate 是否能降低 browser-to-CLI prompt injection 風險？

### RQ5

Skill graph / DAG execution 是否能比 flat skill list 更適合多步任務？

---

## 5. 不解決的問題

第一版專題不處理：

- 真正 production 級雲端部署。
- 金流、自動購物、自動登入敏感帳號。
- 大規模 reinforcement learning。
- 完全無人審核的高風險 shell 自動更新。
- 任意網站通用自動化，只先處理 localhost 與可控 fixtures。
