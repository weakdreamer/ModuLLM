"""Core data contracts for messages and sessions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    role: str
    content: str
    timestamp: str


@dataclass
class Session:
    session_id: str
    title: str
    draft: str = ""
    messages: List[Message] = field(default_factory=list)


@dataclass
class SessionSummary:
    session_id: str
    title: str


CommTarget = str
Payload = dict
