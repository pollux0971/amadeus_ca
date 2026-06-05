# Research Notes

本文件整理本專題採用的研究概念，方便寫報告時引用。

## 1. Harness Engineering

核心觀念：LLM 系統表現不只取決於模型，也取決於外部 harness。  
Harness 決定：

- 要保存什麼。
- 要取回什麼。
- 要呈現什麼給模型。
- 如何記錄 execution trace。
- 如何評估候選版本。

本專題將 harness 作為主設計對象，而非只調 prompt。

---

## 2. ReCAP-style Planning

長任務需要避免 context drift。  
採用：

- plan-ahead decomposition。
- 只執行第一個 subtask。
- subtask 完成後重新注入 parent plan。
- bounded active context。

本專題對應設計：

- `parent_plan`
- `remaining_steps`
- `current_subgoal`
- `context_packet`

---

## 3. Skill Lifecycle

技能不應是一次性 prompt，而應是長期資產。

本專題採用：

- creation
- memory
- management
- evaluation
- refinement

對應目錄：

- `SKILL.md`
- `manifest.yaml`
- `gene.yaml`
- `scripts/`
- `tests/`
- `memory/`

---

## 4. Skill Graph / DAG

Flat skill retrieval 無法描述依賴。  
本專題使用 skill graph edge types：

- prerequisite
- data
- state
- recovery
- enhancement

目標是讓系統不只知道「哪些 skill 相關」，還知道「如何排列與修復」。

---

## 5. Strategy Gene

完整 skill 文件適合人類閱讀，但 runtime 不應塞太長文件。  
因此每個 skill 另有 `gene.yaml`，用短格式提供：

- keywords
- summary
- strategy
- avoid
- validation

---

## 6. Context Router

不同狀態使用不同 context 策略：

- Keep-last-n
- Summary + pinned evidence
- Discard noisy trace + re-inject goal
- Failure report + relevant skill memory

---

## 7. Multi-turn Robustness

多輪欠規格任務容易讓 LLM 早下結論、做錯假設、後續修正不回來。  
本專題使用 sharded tasks 測試 agent 是否能等待完整資訊、更新 plan、避免 premature final answer。
