# Brownfield + Harness Workflow

## Purpose

This document defines how to add new features to an existing agent harness without turning the project into a fragile monolith.
It covers three recurring extension scenarios:

1. Adding a new full-stack interface.
2. Adding a new data input channel.
3. Adding multimodal capabilities such as image, PDF, audio, video, or sensor inputs.

The main rule is simple:

> New material first enters a fixed external intake area, then passes through a harness review, adapter boundary, tests, and promotion gates before it can affect stable runtime behavior.

This workflow is intentionally brownfield-friendly. It assumes you will frequently add open-source projects, datasets, UI prototypes, papers, screenshots, sensor logs, or multimodal examples after the base system already exists.

---

## Why a Brownfield Workflow Is Needed

A greenfield workflow starts from a clean system and designs everything before coding. Your project will not stay like that.
Over time, you may want to add:

- a React / Next.js dashboard,
- a local web UI for viewing traces,
- API upload endpoints,
- browser extension input,
- file watchers,
- camera or microphone input,
- PDF or slide ingestion,
- open-source browser-use / SWE-agent / OpenHands-style code,
- multimodal model wrappers,
- new benchmark fixtures.

If every new thing is copied directly into `src/`, the harness will become untestable. The brownfield workflow prevents this by forcing new material through a stable intake pipeline.

---

## Fixed Locations

All external material must start under `external/`.

```text
external/
├── inbox/
│   ├── raw/              # newly dropped files, repos, archives, datasets
│   └── manifests/        # source metadata written by the user or intake script
├── staging/              # unpacked or normalized material under review
├── approved/             # safe, reviewed material referenced by adapters
├── projects/             # cloned open-source projects or references to them
├── datasets/             # tabular/text datasets, logs, benchmark data
└── multimodal/           # images, PDFs, audio, video, sensor streams
```

Do not let runtime agents read arbitrary local directories. The harness should only expose approved, manifest-described sources.

---

## Brownfield Intake Pipeline

```text
Drop source into external/inbox/raw
        ↓
Create external source manifest
        ↓
Quarantine scan and classify
        ↓
Normalize into staging
        ↓
Write adapter proposal
        ↓
Create eval task and fixture
        ↓
Run unit + integration + safety tests
        ↓
Promote to approved
        ↓
Enable through extension registry
```

The important part is that the harness does not integrate a new source directly. It integrates an adapter that knows how to read that source safely.

---

## New Feature Proposal Flow

Every new feature gets a small proposal file before code is added.

```text
specs/extensions/proposals/<feature_id>.md
```

A proposal should answer:

- What user problem does this solve?
- Is this UI, data input, multimodal input, agent capability, or evaluation infrastructure?
- Which stable modules are touched?
- Which new adapter is required?
- What evidence proves it works?
- What is the rollback plan?
- What budgets must it obey?

---

## Full-Stack UI Extension Flow

A full-stack interface must be treated as a separate surface, not as the agent core.

Recommended structure:

```text
apps/
└── web_console/
    ├── README.md
    ├── package.json
    ├── src/
    └── tests/
```

The UI should talk to the harness through stable APIs:

```text
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/skills
POST /api/evals/run
POST /api/external/intake
```

The UI must not directly modify:

```text
skills/
specs/
src/agents/
src/harness/safety_gate
harnesses/stable
```

The UI can propose changes through candidate workspaces and promotion policy.

---

## New Data Channel Flow

Examples:

- CSV upload,
- PDF upload,
- browser extension capture,
- Gmail / Calendar / API connector,
- sensor stream,
- local folder watcher,
- user drag-and-drop.

Every input channel must implement the same adapter contract:

```text
source → normalize → artifact refs → evidence store → context packet
```

The channel should output normalized `ArtifactRef` objects, not raw data directly into prompts.

---

## Multimodal Extension Flow

Multimodal content should be normalized into artifacts first:

```text
image/audio/video/pdf/sensor file
        ↓
artifact metadata
        ↓
derived text summary or feature extraction
        ↓
evidence refs
        ↓
retrieved only when needed
```

The default policy is:

- Store raw files externally.
- Generate lightweight metadata.
- Pin critical evidence.
- Do not inject full OCR / transcript / frame dumps into context.
- Keep raw file references for audit and replay.

---

## Harness Adjustments Required

Adding new features requires adjustment in these places:

1. **Extension Registry**: register the new adapter.
2. **Context Router**: decide when the new source appears in context.
3. **Evidence Store**: store derived evidence and raw refs.
4. **Safety Gate**: define trust level and allowed operations.
5. **Eval Task**: create a regression case proving the feature works.
6. **Efficiency Metrics**: track extra tokens, latency, storage, tool calls.
7. **Promotion Policy**: define when it can move from staging to stable.

---

## Brownfield Rule of Thumb

A new feature is not complete when it works once.

It is complete when:

- it has a manifest,
- it has an adapter,
- it has a fixture,
- it has an eval task,
- it has tests,
- it logs trace events,
- it respects context budgets,
- it can be disabled or rolled back.
