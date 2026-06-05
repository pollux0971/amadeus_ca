from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

ExtensionCategory = Literal[
    "interface",
    "data_channel",
    "multimodal_processor",
    "tool_provider",
    "skill_provider",
    "eval_provider",
    "report_provider",
]


@dataclass(frozen=True)
class ExtensionDescriptor:
    extension_id: str
    category: ExtensionCategory
    entrypoint: str
    risk_level: str = "low"
    enabled: bool = False
    required_evals: tuple[str, ...] = ()
    budget_keys: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["required_evals"] = list(self.required_evals)
        data["budget_keys"] = list(self.budget_keys)
        return data


class ExtensionRegistry:
    def __init__(self) -> None:
        self._items: dict[str, ExtensionDescriptor] = {}

    def register(self, descriptor: ExtensionDescriptor) -> None:
        if not descriptor.extension_id:
            raise ValueError("extension_id is required")
        if descriptor.extension_id in self._items:
            raise ValueError(f"extension already registered: {descriptor.extension_id}")
        self._items[descriptor.extension_id] = descriptor

    def get(self, extension_id: str) -> ExtensionDescriptor:
        return self._items[extension_id]

    def enabled(self) -> list[ExtensionDescriptor]:
        return [item for item in self._items.values() if item.enabled]

    def by_category(self, category: ExtensionCategory) -> list[ExtensionDescriptor]:
        return [item for item in self._items.values() if item.category == category]

    def list_all(self) -> list[dict]:
        return [item.to_dict() for item in self._items.values()]


def validate_extension_descriptor(descriptor: ExtensionDescriptor) -> list[str]:
    errors: list[str] = []
    if not descriptor.extension_id:
        errors.append("extension_id is required")
    if not descriptor.entrypoint:
        errors.append("entrypoint is required")
    if descriptor.risk_level not in {"low", "medium", "high"}:
        errors.append("risk_level must be low, medium, or high")
    if descriptor.risk_level == "high" and not descriptor.required_evals:
        errors.append("high risk extensions require evals")
    return errors
