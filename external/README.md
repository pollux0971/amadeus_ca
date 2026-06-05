# External Source Area

This directory is the fixed brownfield intake location.

Do not give runtime agents arbitrary access to your whole computer. Put external material here first, describe it with a manifest, and promote it only after tests and safety checks.

## Layout

```text
external/
├── inbox/raw/          # newly dropped files, archives, datasets, cloned repos
├── inbox/manifests/    # source manifests
├── staging/            # normalized but not yet approved material
├── approved/           # reviewed sources available to adapters
├── projects/           # open-source project snapshots or references
├── datasets/           # datasets and structured data
└── multimodal/         # images, PDFs, audio, video, sensor logs
```

## Rule

Raw source is not runtime context. Runtime context is created through adapters, artifact refs, evidence refs, and context routing.
