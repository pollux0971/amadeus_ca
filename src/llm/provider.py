"""Abstract LLM provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .types import LLMRequest, LLMResponse


class LLMProvider(ABC):
    """Provider interface. Implementations must never log/return secrets.

    Required attributes:
      - provider_name: str
      - model: str
      - real_api_enabled: bool   (False for fake / blocked providers)
      - redaction_enabled: bool
    """

    provider_name: str = "base"

    def __init__(self, model: str = "", real_api_enabled: bool = False,
                 redaction_enabled: bool = True):
        self.model = model
        self.real_api_enabled = real_api_enabled
        self.redaction_enabled = redaction_enabled

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Return a completion for the request. No network for fake providers."""
        raise NotImplementedError
