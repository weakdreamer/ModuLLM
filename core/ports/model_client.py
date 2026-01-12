"""Model client port defines how chat completions are requested."""
from __future__ import annotations

from typing import Protocol, List, Dict, Any

from .types import Message


class ModelClientPort(Protocol):
    def send_chat(self, messages: List[Message], cfg: Dict[str, Any] | None = None) -> str:
        """Send chat messages to a model provider and return the reply text."""
