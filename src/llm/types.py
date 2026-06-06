"""LLM types — pure dataclasses, no external dependencies, no secrets."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMUsage:
    input_chars: int = 0
    output_chars: int = 0
    estimated_tokens: int = 0


@dataclass
class LLMRequest:
    messages: list[LLMMessage] = field(default_factory=list)
    model: str = ""
    max_tokens: int = 512
    metadata: dict = field(default_factory=dict)

    @property
    def prompt_text(self) -> str:
        return "\n".join(m.content for m in self.messages)


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    usage: LLMUsage
    redacted: bool = False
    metadata: dict = field(default_factory=dict)


class LLMProviderError(Exception):
    """Raised for provider construction / call problems (e.g. fail-closed)."""
