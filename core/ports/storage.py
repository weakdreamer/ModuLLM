"""Storage port abstracts session and message persistence."""
from __future__ import annotations

from typing import Protocol, List

from .types import Message, Session, SessionSummary


class StoragePort(Protocol):
    def list_sessions(self) -> List[SessionSummary]:
        """Return summaries of all sessions."""

    def get_session(self, session_id: str) -> Session:
        """Return a session with messages; create fallback if missing."""

    def create_session(self, title: str = "New Session") -> str:
        """Create a session and return its id."""

    def save_session(self, session: Session) -> None:
        """Persist an entire session (metadata and messages)."""

    def append_message(self, session_id: str, role: str, content: str) -> None:
        """Append a message to a session."""

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and return True if removed."""

    def clear_all_sessions(self) -> None:
        """Remove all sessions and messages."""

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """Rename a session title."""
