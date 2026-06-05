# Project Brief

## 專題名稱

**基於 Harness Engineering 的 CLI 與 Browser 多代理技能測試系統**

英文名稱：

**A Harness-Engineered Multi-Agent System for CLI-Browser Automation with Self-Evolving Skills**

---

## 一句話介紹

本專題設計一套能讓 LLM agent 安全操作本地 CLI 與外部 Browser，並透過 skill package、trace logging、benchmark evaluation 與自動修復流程持續改進自身能力的 agent harness。

---

## 核心問題

一般 LLM agent 雖然能呼叫工具，但在長任務中常出現：

1. 忘記高階目標。
2. 被 CLI log、Browser DOM、錯誤訊息淹沒。
3. 使用沒有測試的技能。
4. 無法判斷自己是否真的完成任務。
5. 失敗後缺少可追蹤資料，難以改進。
6. Browser prompt injection 可能污染 CLI 操作。
7. Claude Code / Codex 可以改程式，但缺乏系統化測試與升級流程。

---

## 專題目標

本系統要建立一個「agent 外部控制層」，負責：

- 管理 agent 可以看到的 context。
- 管理 agent 可以使用的 skills。
- 管理 CLI / Browser 的權限邊界。
- 記錄每一步 action / observation / artifact。
- 自動評分、產生 failure report。
- 讓 Claude Code / Codex 產生 candidate patch。
- 經由測試與 promotion policy 決定是否升級。

---

## 系統輸入

- 使用者任務，例如：修復本地 web app 登入頁錯誤。
- Skill registry。
- Benchmark task YAML。
- Fixtures 測試專案。
- Safety policy。
- Context budget。
- Optional：Claude Code / Codex patch agent。

---

## 系統輸出

- 最終任務結果。
- `runs/<run_id>/trace.jsonl`
- `runs/<run_id>/score.json`
- `runs/<run_id>/summary.md`
- `runs/<run_id>/failure_report.md`
- Candidate patch。
- Promotion decision。

---

## 最重要 Demo

### Demo 1：Skill Package Runner

證明 skill 是可測試資產，不是單純 prompt。

### Demo 2：CLI + Browser 修 Bug

系統啟動本地 Vite app，Browser 讀 console error，CLI 修改 source file，重新測試與驗證。

### Demo 3：Auto Skill Repair

故意提供壞掉 skill，讓 Claude Code / Codex 根據 failure report 修復 candidate，再由測試判斷是否升級。

---

## 預期成果

1. 一個可執行的 multi-agent harness prototype。
2. 一組 skill package 格式與範例技能。
3. 一組 CLI + Browser benchmark tasks。
4. 一套 trace / score / failure report 格式。
5. 一個自動修復與 candidate promotion 流程。
6. 一份完整專題報告與 demo video。
