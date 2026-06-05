# Evaluation Plan

## 1. 任務層指標

| 指標 | 說明 |
|---|---|
| task_success | 任務是否完成 |
| pass@1 | 單次執行是否成功 |
| average_steps | 平均步數 |
| runtime_sec | 執行時間 |
| cli_command_count | CLI 命令數 |
| browser_action_count | Browser 行為數 |
| token_cost | LLM token 成本 |

---

## 2. 可靠性指標

| 指標 | 說明 |
|---|---|
| failure_recovery_rate | 失敗後修復成功率 |
| regression_rate | 更新後退步比例 |
| flaky_rate | 同任務多次跑結果不一致比例 |
| repeated_loop_count | 重複無效操作次數 |
| premature_final_answer_count | 過早宣稱完成次數 |

---

## 3. Skill 層指標

| 指標 | 說明 |
|---|---|
| skill_unit_test_pass_rate | skill unit tests 通過率 |
| skill_reuse_count | skill 被重用次數 |
| skill_success_rate | skill 在任務中的成功率 |
| skill_update_success_rate | skill 修復後通過率 |
| skill_deprecation_count | 被淘汰技能數 |

---

## 4. 安全指標

| 指標 | 說明 |
|---|---|
| dangerous_command_blocked | 阻擋危險 command 次數 |
| secret_leak_count | secret 外洩次數 |
| prompt_injection_detected | 偵測 prompt injection 次數 |
| prompt_injection_success_rate | 攻擊成功率，越低越好 |
| human_review_triggered | 需要人工審核次數 |

---

## 5. Baseline Comparison

建議比較三種模式：

1. Baseline ReAct agent。
2. Harness without skills。
3. Harness with skill packages。
4. Harness with skill packages + auto repair。

每個 task 至少跑 3 次，避免 flaky 結果。

---

## 6. 必備評估任務

### CLI-only

- Python failing test 修復。
- Missing dependency 檢查。
- Shell command safety。

### Browser-only

- DOM summary。
- Console error 擷取。
- Button click state verification。

### CLI + Browser

- Vite login bug。
- Port conflict。
- Browser console error to source map。

### Adversarial

- Malicious README。
- Browser prompt injection。
- Secret access attempt。

### Multi-turn

- Sharded user goal。
- Late constraint injection。
- Recap / snowball context test。
