from __future__ import annotations

import json
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def load_yaml(path: str | Path) -> dict:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
        return data or {}

    # Fallback: very small subset YAML reader for this scaffold.
    # It supports top-level keys, nested maps, and lists of strings.
    result: dict = {}
    stack: list[tuple[int, object]] = [(-1, result)]
    last_key_at_indent: dict[int, str] = {}

    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        if line.startswith("- "):
            item = line[2:].strip().strip('"').strip("'")
            if isinstance(parent, list):
                parent.append(item)
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                new_obj: dict | list = {}
                if isinstance(parent, dict):
                    parent[key] = new_obj
                stack.append((indent, new_obj))
                last_key_at_indent[indent] = key
            else:
                parsed: object
                if value in {"true", "false"}:
                    parsed = value == "true"
                elif value.isdigit():
                    parsed = int(value)
                else:
                    parsed = value.strip('"').strip("'")
                if isinstance(parent, dict):
                    parent[key] = parsed
    return result


def dump_json(data: object, path: str | Path) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
