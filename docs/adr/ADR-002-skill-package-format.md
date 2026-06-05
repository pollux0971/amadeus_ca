# ADR-002: Skill Package Format

## Status

Accepted

## Context

Skill 可以是 markdown、prompt、script 或完整 package。  
本專題希望 skills 可測試、可版本化、可註冊、可修復。

## Decision

每個 skill 使用資料夾 package：

```text
skill_id/
├── SKILL.md
├── manifest.yaml
├── gene.yaml
├── scripts/
├── tests/
├── evals/
└── memory/
```

## Consequences

優點：

- Skill 可被 unit test 驗證。
- Manifest 可被機器讀取。
- Gene 可作為 runtime context。
- Memory 可累積成功與失敗經驗。

缺點：

- 每個 skill 建立成本較高。
- 需要 validator 與 test runner。
