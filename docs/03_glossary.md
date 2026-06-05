# Glossary

## Agent

負責某類任務的 LLM-based 或 rule-based 執行單元。

## Harness

包在 LLM 外面的控制程式，負責 context construction、tool selection、skill routing、trace logging、evaluation、promotion。

## Skill

可重用、可測試、可版本化的能力單元。

## Skill Package

一個資料夾，通常包含：

- `SKILL.md`
- `manifest.yaml`
- `gene.yaml`
- `scripts/`
- `tests/`
- `evals/`
- `memory/`

## SKILL.md

完整技能文件，給人類與 agent 工程師閱讀。

## Manifest

機器可讀的 skill 規格，包含 input/output、權限、entrypoint、tests、risk level。

## Gene

Runtime 注入給模型的短控制表示，重點是高密度策略、avoid cues、validation hooks。不是完整文件。

## Skill Registry

系統掃描所有 skills 後產生的可用技能清單。

## Skill Graph

skills 之間的依賴圖，包含 prerequisite、data、state、recovery、enhancement 等邊。

## Context Packet

每一步交給 agent 的結構化上下文。

## Shared Blackboard

多 agent 共享的任務狀態，不包含高風險 raw secrets。

## Trace

一次任務執行的完整紀錄，包含 action、observation、artifact、score、error。

## Evidence Ref

指向某個可驗證 artifact 的引用，例如 browser console log、screenshot、test output。

## Candidate

Claude Code / Codex 產生的待測試修改版本。

## Promotion

候選修改通過測試後升級到 dev、staging 或 stable。

## Safety Gate

阻擋危險行為的模組，尤其是 shell command、secret、browser prompt injection。

## Fixture

可重複還原的測試專案或測試網頁。

## Benchmark Task

用 YAML 描述的可重複測試任務。

## Failure Report

任務失敗後產生的診斷文件，提供 coding agent 修復依據。
