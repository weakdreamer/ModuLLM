"""Prompt management port for injecting system prompts."""
from __future__ import annotations

from typing import Protocol, List

from .types import Message


class PromptPort(Protocol):
    def get_system_prompt(self, name: str) -> Message | None:
        """Return a system prompt message by name or None if not found."""

    def apply_prompt(self, messages: List[Message], prompt_name: str) -> List[Message]:
        """Return a new message list with the system prompt (if any) prepended."""
