# Development Roadmap

## 開發總策略

不要一開始就寫複雜 multi-agent。先讓基礎設施穩定：

1. 文件與規格。
2. Skill package runner。
3. Trace logger。
4. CLI agent。
5. Browser agent。
6. Verifier / evaluator。
7. CLI + Browser integration demo。
8. Auto repair loop。

---

## M0. Project Skeleton

### 目標

建立完整專案目錄、文件入口與最小測試。

### 交付

- `README.md`
- `docs/`
- `specs/`
- `src/`
- `skills/`
- `evals/`
- `fixtures/`
- `scripts/validate_structure.py`

### 完成條件

```bash
python scripts/validate_structure.py
```

成功輸出：

```text
[PASS] project structure is complete
```

---

## M1. Skill Package Runner

### 目標

能載入、驗證、測試 skill package。

### 交付

- `src/skills_runtime/loader.py`
- `src/skills_runtime/validator.py`
- `src/skills_runtime/registry.py`
- `scripts/run_skill_tests.py`
- `skills/inspect_project/`

### 完成條件

```bash
python scripts/run_skill_tests.py
```

成功輸出：

```text
[PASS] inspect_project
Generated .cache/skill_registry.json
```

---

## M2. CLI Agent Harness

### 目標

讓系統能安全執行 CLI 任務。

### 交付

- CLI command runner。
- Safety Gate。
- stdout / stderr capture。
- command timeout。
- git diff capture。

### 完成條件

- `pytest` 可執行。
- `npm run dev` 可執行。
- `rm -rf` 被阻擋。
- `cat .env` 被阻擋。
- `curl | bash` 被阻擋。

---

## M3. Browser Agent Harness

### 目標

讓系統能操作 browser 並收集 evidence。

### 交付

- Browser controller。
- DOM summary。
- console reader。
- screenshot artifact。
- browser trace artifact。

### 完成條件

- 能打開 localhost。
- 能讀 console error。
- 能保存 screenshot。
- 能輸出 evidence_refs。

---

## M4. CLI + Browser Integration Demo

### 目標

完成專題核心 demo：修復本地 web app bug。

### 任務

1. CLI inspect project。
2. CLI start server。
3. Browser open localhost。
4. Browser read console error。
5. CLI patch source file。
6. CLI run tests。
7. Browser verify again。
8. Verifier score。

### 完成條件

- 修 bug 前有 console error。
- 修 bug 後 tests pass。
- 修 bug 後 browser fatal error 消失。
- run folder 產生完整 report。

---

## M5. Auto Skill Repair Loop

### 目標

讓 Claude Code / Codex 根據測試失敗修復 skill 或 harness。

### 交付

- failure report generator。
- candidate workspace。
- candidate evaluation。
- baseline comparison。
- promotion policy。

### 完成條件

故意破壞 `start_local_server` skill 後：

1. tests fail。
2. failure_report 產生。
3. candidate patch 產生。
4. tests pass。
5. candidate promote to staging。

---

## M6. Context Router / Multi-turn Robustness

### 目標

處理多輪補充需求，避免 agent 太早亂修或忘記後續需求。

### 交付

- sharded task runner。
- context recap policy。
- parent plan reinjection。
- premature answer detector。

### 完成條件

Agent 能整合多輪補充任務，最後完整滿足所有 constraints。
