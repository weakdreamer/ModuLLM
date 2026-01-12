"""Config port abstracts configuration persistence."""
from __future__ import annotations

from typing import Protocol, Dict, Any


class ConfigPort(Protocol):
    def load(self) -> Dict[str, Any]:
        """Load configuration data."""

    def save(self, cfg: Dict[str, Any]) -> None:
        """Persist configuration data."""
