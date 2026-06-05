# Memory Policy

## Purpose

This policy defines how the system stores and retrieves execution memory.

---

## Memory Layers

### Raw Artifacts

Full logs, traces, screenshots, browser traces, and diffs. Never inject raw artifacts directly unless small and relevant.

### Sensory Memory

Short filtered observations extracted from raw artifacts.

### Short-Term Task Memory

Current task state, pinned evidence, current plan, and recent observations.

### Long-Term Skill Memory

Per-skill success/failure notes accumulated across runs.

### Harness Memory

Lessons about context routing, tool budget, and planner failures.

---

## Online Update Rule

During task execution:

```text
append only
```

Do not merge, delete, or rewrite long-term memory during active task execution.

---

## Sleep-Time Update Rule

After task completion:

- deduplicate repeated failures,
- merge related notes,
- update skill success statistics,
- extract failure patterns,
- suggest skill graph changes,
- update harness candidate notes.

---

## Memory Retrieval Rule

Retrieve memory only when it affects current decision quality.

Prefer:

- current skill memory,
- current task type memory,
- matching error signature memory,
- pinned evidence.

Avoid:

- old unrelated logs,
- full raw trajectories,
- unverified browser content,
- stale skill notes.
