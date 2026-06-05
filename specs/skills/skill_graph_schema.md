# Skill Graph Schema

## Purpose

Skill graph 描述 skills 的依賴關係。  
它讓系統不只知道「哪些 skills 相關」，還知道「怎麼排列、怎麼傳資料、失敗時怎麼修」。

---

## Node

```yaml
skill_node:
  id: string
  version: string
  level: planning | functional | atomic
  status: draft | tested | staging | stable | deprecated
  success_rate: float
  usage_count: integer
```

---

## Edge Types

### prerequisite

A must run before B.

### data

A output becomes B input.

### state

A creates environment state required by B.

### recovery

If B fails, try A.

### enhancement

A improves B but is optional.

---

## Edge

```yaml
skill_edge:
  from: string
  to: string
  type: prerequisite | data | state | recovery | enhancement
  weight: float
  evidence:
    - run_id: string
      note: string
```

---

## Execution Rule

The graph compiler should:

1. retrieve relevant skills
2. expand prerequisites
3. topologically sort
4. attach pre/postcondition checks
5. create executable plan
6. allow local repair when a node fails
