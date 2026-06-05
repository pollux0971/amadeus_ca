# START HERE — 從零開始實作順序

這份專案不是要你一開始就寫一個巨大 agent，而是先做一個可以被測試、被記錄、被擴充的 **agent harness skeleton**。

如果你今天從零開始，請照下面順序做，不要跳過。

---

## 0. 先理解兩條工作流

本專案有兩條主工作流：

1. **0→1 工作流**：從空 repo 做出第一個可跑的 vertical slice。
2. **1→N 工作流**：在既有 harness 上新增功能、資料渠道、UI、多模態、外部開源專案整合。

對應文件：

- `docs/14_zero_to_one_workflow.md`
- `docs/15_one_to_n_workflow.md`
- `docs/11_brownfield_harness_workflow.md`
- `specs/workflows/zero_to_one_contract.md`
- `specs/workflows/one_to_n_contract.md`

---

## 1. 第一天只做這些

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
pip install -e .
pytest -q
python scripts/validate_structure.py
python scripts/validate_workflows.py
python scripts/run_skill_tests.py
```

如果這些都 pass，代表專案骨架是健康的。

---

## 2. 第一個目標不是完整 agent，而是 walking skeleton

第一個可展示目標：

```text
讀取 eval task
→ 載入 skill registry
→ 執行 inspect_project skill
→ 產生 trace.jsonl
→ evaluator 產生 score.json
```

這個叫 **walking skeleton**。它不需要聰明，但每個核心模組都要被串到。

---

## 3. 第一個真正 demo 是 thin vertical slice

第一個完整 demo：

```text
fixture: fixtures/vite_login_bug
任務: 修復 Vite/React login bug
流程:
1. InspectProject
2. StartLocalServer
3. OpenLocalhostBrowser
4. ReadBrowserConsole
5. PatchFileAndRunTests
6. Verify result
7. Generate report
```

對應 eval：

```text
evals/cli_browser_integration/vite_login_bug.yaml
```

---

## 4. 實作規則

每次新增功能都必須先回答：

```text
這是 0→1 還是 1→N？
這是 core harness 還是 extension？
它的 input/output schema 在哪裡？
它的 eval task 在哪裡？
它會不會碰 CLI、Browser、外部資料、secret 或 user file？
```

如果是 1→N，請不要直接改 `src/orchestrator/` 或 `src/agents/`。先走：

```text
external/inbox/raw
→ external/inbox/manifests
→ brownfield intake
→ adapter
→ eval
→ staging
→ approved
```

---

## 5. 你最常看的文件

```text
START_HERE.md
README.md
FILE_INDEX.md
docs/14_zero_to_one_workflow.md
docs/15_one_to_n_workflow.md
docs/11_brownfield_harness_workflow.md
specs/harness/harness_contract.md
specs/skills/skill_package_spec.md
specs/extensions/extension_adapter_spec.md
specs/workflows/zero_to_one_contract.md
specs/workflows/one_to_n_contract.md
```

---

## 6. 完成 0→1 的判斷標準

0→1 完成不是「程式很多」，而是：

- 有一個可跑 demo。
- 有 trace。
- 有 score。
- 有至少 5 個 skill packages。
- 有 CLI + Browser bridge。
- 有 Safety Gate。
- 有 eval task。
- 有 regression check。

---

## 7. 完成 1→N 的判斷標準

1→N 完成不是「把功能塞進去」，而是：

- 新功能有 feature intake。
- 外部資料有 source manifest。
- 新功能透過 adapter 接入。
- 有最小 eval task。
- 有安全檢查。
- 有 budget 檢查。
- 不破壞原本 demo。
- 能被 rollback。

