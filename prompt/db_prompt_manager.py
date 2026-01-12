"""Prompt manager backed by Storage prompts table."""
from __future__ import annotations

import datetime
from typing import List

from core.ports import PromptPort, Message
from storage import Storage


class DbPromptManager(PromptPort):
    def __init__(self, storage: Storage):
        self.storage = storage

    def get_system_prompt(self, name: str) -> Message | None:
        record = self.storage.get_prompt(name)
        if not record:
            return None
        # System prompt timestamp uses creation time placeholder
        ts = datetime.datetime.now(datetime.UTC).isoformat()
        return Message(role=record.get("role", "system"), content=record.get("content", ""), timestamp=ts)

    def apply_prompt(self, messages: List[Message], prompt_name: str) -> List[Message]:
        prompt_msg = self.get_system_prompt(prompt_name)
        if not prompt_msg:
            return list(messages)
        return [prompt_msg, *messages]
