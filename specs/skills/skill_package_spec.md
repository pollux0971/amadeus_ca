# Skill Package Spec

## 1. Purpose

Skill package 是本系統的基本能力單元。  
每個 skill 都必須可描述、可測試、可執行、可驗證、可版本化。

---

## 2. Required Structure

```text
skills/<skill_id>/
├── SKILL.md
├── manifest.yaml
├── gene.yaml
├── scripts/
├── tests/
├── evals/
└── memory/
```

---

## 3. Required Files

### SKILL.md

完整說明，包含：

- purpose
- when to use
- inputs
- outputs
- preconditions
- procedure
- failure modes
- recovery
- safety notes

### manifest.yaml

機器可讀規格，包含：

- id
- version
- level
- domain
- entrypoint
- inputs
- outputs
- permissions
- risk_level
- preconditions
- postconditions
- tests

### gene.yaml

Runtime 控制表示，包含：

- keywords
- summary
- strategy
- avoid
- validation

### scripts/

可選。放 skill 的實作程式。

### tests/

必要。至少要有一個 unit test 或 validation test。

### evals/

可選。放此 skill 的 integration benchmark。

### memory/

可選但建議。保存成功與失敗經驗。

---

## 4. Skill Levels

### planning

高階規劃技能，例如「如何拆解 web app debugging 任務」。

### functional

可完成一個子任務，例如「啟動本地 server」。

### atomic

接近工具使用規則，例如「如何安全執行 shell command」。

---

## 5. Skill Status

```yaml
status: draft | tested | staging | stable | deprecated
```

---

## 6. Validation Rules

A skill is valid only if:

- `SKILL.md` exists.
- `manifest.yaml` exists.
- `gene.yaml` exists.
- manifest id matches folder name.
- risk_level is defined.
- tests path exists.
- required inputs and outputs are documented.
