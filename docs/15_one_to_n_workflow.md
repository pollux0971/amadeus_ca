# 1→N Workflow — 在既有 Harness 上安全擴充功能

本文件定義當專案已經有可跑 harness 之後，如何新增功能，例如：全端介面、資料輸入渠道、多模態功能、外部開源專案整合、新 agent、新 skill 或新 eval。

---

## 1. 1→N 的定義

1→N 指的是：

```text
已有穩定 0→1 vertical slice
→ 新增一個功能或外部資源
→ 不破壞既有 demo
→ 新功能透過 adapter / manifest / eval / promotion gate 接入
```

1→N 的關鍵不是「加功能」，而是 **不讓新功能污染核心 harness**。

---

## 2. 什麼情況屬於 1→N？

以下都屬於 1→N：

```text
新增全端 dashboard
新增 CSV / PDF / image / audio / video input channel
接入一個 GitHub 開源專案
新增 browser-use backend
新增 Playwright adapter
新增多模態模型
新增 vector database
新增 Claude Code / Codex auto repair loop
新增一個 agent role
新增一組 skills
新增一組 benchmark evals
```

---

## 3. 1→N 的總流程

```text
Feature Idea
  ↓
Feature Intake
  ↓
External Source Manifest
  ↓
Quarantine / Brownfield Inspection
  ↓
Impact Analysis
  ↓
Adapter Design
  ↓
Contract Tests
  ↓
Minimal Eval Task
  ↓
Implementation in Candidate Branch
  ↓
Regression + Safety + Budget Check
  ↓
Promotion to Staging
  ↓
Manual Review if High Risk
  ↓
Approved Runtime Use
```

---

## 4. Step 1 — Feature Intake

每個新功能先寫 intake，不直接寫 code。

位置：

```text
external/inbox/manifests/<feature_id>_feature_intake.yaml
```

或使用模板：

```text
templates/feature_intake/feature_intake_template.yaml
```

Feature intake 至少要回答：

```yaml
feature_id: string
feature_type: fullstack_ui | data_channel | multimodal | external_project | new_skill | new_agent | other
problem_statement: string
user_value: string
sources: list
expected_runtime_surface: cli | browser | api | ui | multimodal | data
risk_level: low | medium | high
requires_new_adapter: bool
requires_new_skill: bool
requires_new_eval: bool
success_criteria: list
rollback_plan: string
```

---

## 5. Step 2 — External Source Manifest

如果你要加入資料、開源專案、圖片、PDF、UI template，都必須先寫 source manifest。

位置：

```text
external/inbox/manifests/<source_id>.yaml
```

外部資料本體放：

```text
external/inbox/raw/<source_id>/
```

不要直接放到：

```text
src/
skills/
apps/
```

---

## 6. Step 3 — Quarantine / Brownfield Inspection

外部專案或資料先進 quarantine，不直接使用。

檢查項目：

```text
license
README
install script
package scripts
Dockerfile
.env.example
secret-like strings
network calls
postinstall hooks
binary files
large files
unknown model weights
```

輸出：

```text
external/staging/<source_id>/inspection_report.md
```

---

## 7. Step 4 — Impact Analysis

新增功能前必須判斷會碰到哪些核心模組。

分類：

```text
No-core-change:
  只新增 adapter、eval、fixture，不改 core harness

Small-core-change:
  需要新增 registry hook 或 schema field

High-risk-core-change:
  需要改 safety gate、orchestrator、promotion policy、command runner
```

高風險改動不能自動 promote。

---

## 8. Step 5 — Adapter Design

1→N 的核心原則：**新功能透過 adapter 接入，不直接改核心**。

Adapter 應包含：

```yaml
adapter_id: string
input_schema: object
output_schema: object
permissions: object
risk_level: low | medium | high
entrypoint: string
health_check: string
artifact_policy: object
timeout_policy: object
```

對應規格：

```text
specs/extensions/extension_adapter_spec.md
```

---

## 9. Step 6 — Contract Tests

寫實作前先寫測試。

每個 extension 至少有：

```text
schema validation test
adapter health check test
permission boundary test
artifact reference test
budget test
```

不要只測 happy path。

---

## 10. Step 7 — Minimal Eval Task

新增功能一定要有 eval。

範例：

```text
全端 UI:
  evals/brownfield/fullstack_ui_extension.yaml

CSV data channel:
  evals/brownfield/new_data_channel_csv_ingest.yaml

PDF multimodal:
  evals/multimodal/pdf_artifact_extraction.yaml

image input:
  evals/multimodal/image_input_channel_smoke.yaml
```

Eval 至少要定義：

```yaml
user_goal: string
fixture: object
required_artifacts: list
success_criteria: list
forbidden_actions: list
budget: object
```

---

## 11. Step 8 — Candidate Implementation

所有 1→N 改動先進 candidate。

建議位置：

```text
harnesses/candidates/<candidate_id>/
```

或使用 branch：

```text
feature/<feature_id>
```

Candidate 必須包含：

```text
candidate_summary.md
changed_files.txt
tests_run.txt
risk_report.md
rollback_plan.md
```

---

## 12. Step 9 — Regression + Safety + Budget Check

合併前必跑：

```bash
pytest -q
python scripts/validate_structure.py
python scripts/validate_workflows.py
python scripts/run_skill_tests.py
python scripts/run_eval.py --suite regression
python scripts/run_eval.py --suite adversarial
```

檢查：

```text
舊 demo 是否仍通過
新 eval 是否通過
dangerous command 是否被阻擋
secret 是否沒有外洩
tool call 是否沒有暴增
context 是否沒有超 budget
runtime 是否可接受
```

---

## 13. Step 10 — Promotion

Promotion 分三層：

```text
dev:
  可以實驗

staging:
  通過測試，可被 demo 使用

approved/stable:
  可作為正式能力
```

高風險項目需要人工確認：

```text
修改 safety gate
修改 command runner
允許新的 shell 權限
新增外部 network call
讀取 secrets
修改 promotion policy
```

---

## 14. 新增全端介面的特別規則

全端 UI 不可以直接控制核心檔案。

UI 只能透過 API 呼叫：

```text
GET /api/runs
GET /api/runs/{id}
GET /api/skills
POST /api/evals/run
POST /api/features/intake
```

UI 不可直接：

```text
修改 stable skill
修改 safety gate
執行任意 shell
讀取 .env
promote candidate
刪除 runs
```

對應文件：

```text
apps/web_console/API_CONTRACT.md
specs/extensions/fullstack_interface_extension.md
```

---

## 15. 新增資料輸入渠道的特別規則

資料渠道不直接把 raw data 塞入 prompt。

必須轉成：

```yaml
artifact_ref:
  artifact_id: string
  source_id: string
  media_type: text | table | image | audio | video | pdf | repo
  raw_path: string
  summary_path: string | null
  metadata: object
  access_policy: object
```

例如 CSV：

```text
external/inbox/raw/sales_csv_001/data.csv
→ LocalFileDataChannel
→ ArtifactRef
→ summary + schema + sample rows
```

---

## 16. 新增多模態功能的特別規則

多模態輸入先成 artifact，不直接進 LLM context。

```text
image → metadata + thumbnail + optional description + raw_ref
pdf → page refs + text chunks + figure refs
video → clips + timestamps + frame refs
audio → transcript + segments + raw_ref
sensor → schema + sample window + raw_ref
```

關鍵規則：

```text
raw artifact 保存
prompt 只放 summary + artifact_ref
重要證據 pin 到 evidence store
大型檔案不可整包送進 context
```

---

## 17. 新增開源專案的特別規則

開源專案先放：

```text
external/inbox/raw/<repo_id>/
```

必須檢查：

```text
license
install scripts
postinstall
Dockerfile
GitHub Actions
network behavior
binary blobs
.env examples
package manager lockfiles
```

接入方式優先順序：

```text
1. Read-only inspection
2. Adapter wrapper
3. Fixture copy
4. Sandbox execution
5. Core integration 最後才考慮
```

---

## 18. 1→N 完成檢查清單

```text
[ ] feature intake exists
[ ] external source manifest exists if needed
[ ] source stays in external/ until approved
[ ] inspection report exists
[ ] adapter spec exists
[ ] contract tests exist
[ ] eval task exists
[ ] safety policy updated if needed
[ ] budget policy updated if needed
[ ] regression passes
[ ] rollback plan exists
[ ] promotion decision recorded
```

---

## 19. 1→N 的禁止事項

不要：

```text
直接把外部 repo 複製進 src/
直接把 UI 接到 shell runner
新增功能但沒有 eval
新增 data channel 但沒有 artifact_ref
新增 multimodal 但把 raw binary 塞 prompt
跳過 safety gate
把 candidate 直接蓋掉 stable
```

---

## 20. 1→N 的最小成功標準

一個新功能只有在符合以下條件時才算完成：

```text
能被關閉
能被測試
能被回滾
能被追蹤
不破壞原本 demo
不增加未控風險
```

