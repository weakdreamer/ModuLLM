"""WebSocket-based CommPort implementation."""
from __future__ import annotations

import json
import secrets
import threading
import time
from typing import Callable, Optional

import websocket


class WebSocketComm:
    """Lightweight WebSocket client implementing CommPort."""

    def __init__(self, server_url: str, auth_key: str | None = None, reconnect_delay: float = 3.0):
        self.server_url = server_url
        self.auth_key = auth_key or ""
        self.reconnect_delay = reconnect_delay
        self._ws_app: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._on_message: Optional[Callable[[dict], None]] = None

    def start(self) -> None:
        """Start background websocket loop."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop websocket loop and close connection."""
        self._stop_event.set()
        if self._ws_app and self._ws_app.sock:
            try:
                self._ws_app.close()
            except Exception:
                pass

    def send(self, target: str, payload: dict) -> None:
        """Send a JSON payload to the websocket server."""
        if not payload:
            return
        outgoing = dict(payload)
        if target:
            outgoing.setdefault("target", target)
        try:
            message = json.dumps(outgoing)
        except Exception:
            return
        try:
            if self._ws_app and self._ws_app.sock and self._ws_app.sock.connected:
                self._ws_app.send(message)
        except Exception:
            pass

    def on_message(self, handler: Callable[[dict], None]) -> None:
        self._on_message = handler

    # internal
    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._ws_app = websocket.WebSocketApp(
                    self.server_url,
                    header=self._build_headers(),
                    on_message=self._handle_message,
                    on_error=self._handle_error,
                    on_close=self._handle_close,
                )
                self._ws_app.on_open = self._handle_open
                self._ws_app.run_forever()
            except Exception:
                time.sleep(self.reconnect_delay)
            if not self._stop_event.is_set():
                time.sleep(self.reconnect_delay)
        self._ws_app = None

    def _build_headers(self):
        headers = []
        if self.auth_key:
            headers.append(f"X-Auth-Key: {self.auth_key}")
        return headers

    def _handle_message(self, ws, message):
        try:
            data = json.loads(message)
        except Exception:
            return
        if self._on_message:
            try:
                self._on_message(data)
            except Exception:
                pass

    def _handle_error(self, ws, error):
        # Silence errors; reconnect loop handles retries.
        return

    def _handle_close(self, ws, status, msg):
        return

    def _handle_open(self, ws):
        return


def generate_auth_key() -> str:
    """Generate a random auth key for pairing."""
    return secrets.token_urlsafe(24)
