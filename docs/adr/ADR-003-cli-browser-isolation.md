# ADR-003: CLI-Browser Isolation

## Status

Accepted

## Context

Browser 內容常來自不可信來源；CLI 可以操作本機檔案與 secrets。若兩者完全共享 context，browser prompt injection 可能導致 CLI 執行惡意指令。

## Decision

採用 selective isolation：

- Browser Agent 不看 `.env`、shell history、完整檔案系統。
- CLI Agent 不盲信 Browser content。
- Browser content 進入 CLI 前必須標記 `untrusted_web` 並通過 Safety Gate。
- Shared Blackboard 只保存摘要與 verified evidence。

## Consequences

優點：

- 降低 secret leak。
- 降低 prompt injection。
- 容易審計資訊流。

缺點：

- Agent 間溝通成本增加。
- 需要 Evidence Ref 與 Shared Blackboard。
