# ADR-004: Context Routing Policy

## Status

Proposed

## Context

CLI + Browser traces 很長，固定 summary 策略不一定適合所有情況。

## Decision

採用狀態式 Context Router：

- 短任務：Keep-last-n。
- 有重要證據：Summary + pinned evidence。
- Agent 迷路：Discard noisy trace + re-inject goal and plan。
- 測試失敗：Failure report + related trace + relevant skill memory。
- 多輪任務：Parent plan reinjection。

## Consequences

優點：

- 減少 context rot。
- 保留高階目標。
- 讓 failure repair 更聚焦。

缺點：

- 需要 context packet schema。
- 需要更多 trace metadata。
