# ADR-001: Harness-first Architecture

## Status

Accepted

## Context

本專題可以做成「一個很大的 agent prompt」，也可以做成「harness 控制外部流程」。前者快速但難以測試，後者較工程化但可維護。

## Decision

採用 Harness-first Architecture。

Harness 負責：

- context construction
- skill selection
- agent routing
- trace logging
- scoring
- safety
- promotion

LLM agent 只負責在清楚 context 與工具邊界內完成步驟。

## Consequences

優點：

- 容易測試。
- 容易記錄。
- 容易讓 Claude Code / Codex 修改。
- 容易比較 baseline vs candidate。

缺點：

- 初期文件與 schema 較多。
- 開發速度比單 prompt 慢。
