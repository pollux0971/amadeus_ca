# Extension Roadmap

This document describes how the project can grow after the first CLI + Browser harness MVP.

## Extension Levels

### Level 0: Internal Harness Extension

Examples:

- new scorer,
- new context router strategy,
- new trace field,
- new budget rule.

These are low-risk but still require unit tests and regression checks.

### Level 1: New Skill

Examples:

- `extract_pdf_text`,
- `inspect_api_schema`,
- `run_playwright_test`,
- `summarize_multimodal_artifact`.

New skills must follow the skill package format and include `gene.yaml` for short runtime context.

### Level 2: New Data Channel

Examples:

- local folder input,
- CSV upload,
- PDF upload,
- browser extension input,
- API connector.

New channels must produce normalized artifacts and must not bypass the evidence store.

### Level 3: New Interface Surface

Examples:

- full-stack web dashboard,
- desktop GUI,
- CLI TUI,
- browser extension,
- VS Code extension.

Interfaces must call the harness through API contracts. They should not directly mutate stable harness internals.

### Level 4: New Modality

Examples:

- image analysis,
- audio transcription,
- video frame extraction,
- sensor stream analysis,
- multimodal RAG.

New modalities require a modality-specific artifact schema, safety policy, and context compression policy.

### Level 5: External Project Integration

Examples:

- adopting browser-use code,
- integrating an open-source agent framework,
- importing a UI starter project,
- adding Playwright MCP or crawler code.

External code should enter through `external/projects/`, be described by a manifest, then integrated through adapters or isolated services.

---

## Recommended Build Order

1. Add external source intake.
2. Add extension registry.
3. Add data channel adapter contract.
4. Add local file / CSV channel.
5. Add full-stack dashboard as read-only viewer.
6. Add UI actions that trigger evals.
7. Add multimodal artifact references.
8. Add modality-specific skills.
9. Add external project import workflow.
10. Add candidate promotion for feature branches.

---

## Stability Principle

Do not make every new feature part of the core harness.

Core harness should remain small:

```text
orchestrator
context builder
trace logger
evaluator
safety gate
skill runtime
extension registry
```

Everything else should be an extension.
