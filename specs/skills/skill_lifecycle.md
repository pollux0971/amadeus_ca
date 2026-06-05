# Skill Lifecycle

## 1. Creation

Skill can be created manually or by coding agent.

Required output:

- SKILL.md
- manifest.yaml
- gene.yaml
- tests/

---

## 2. Evaluation

Before registration:

- schema validation
- unit tests
- optional integration tests
- safety review

---

## 3. Registration

If tests pass, skill enters registry.

Status progression:

```text
draft → tested → staging → stable
```

---

## 4. Runtime Use

During task execution:

1. Orchestrator retrieves skill gene.
2. Harness builds context packet.
3. Skill runner executes script or agent procedure.
4. Verifier checks postcondition.
5. Trace logger records result.

---

## 5. Memory Update

After each use:

- usage_count++
- success/failure note added
- failure type recorded
- edge weights may update

---

## 6. Refinement

When skill fails:

- generate failure report
- create candidate patch
- run tests
- compare baseline
- promote or reject

---

## 7. Deprecation

Deprecate if:

- repeated failure
- unsafe behavior
- superseded by better skill
- tests no longer pass
