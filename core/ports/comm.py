"""Communication port for sending/receiving payloads."""
from __future__ import annotations

from typing import Protocol, Callable

from .types import CommTarget, Payload


class CommPort(Protocol):
    def start(self) -> None:
        """Start communication resources (connections, listeners)."""

    def stop(self) -> None:
        """Stop communication resources and clean up."""

    def send(self, target: CommTarget, payload: Payload) -> None:
        """Send a payload to a target endpoint."""

    def on_message(self, handler: Callable[[Payload], None]) -> None:
        """Register a handler for incoming payloads."""
