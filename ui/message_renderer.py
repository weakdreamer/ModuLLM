"""Message list manager that owns MessageBubble instances."""
from typing import List, Dict
import tkinter as tk
from .bubble import MessageBubble


class MessageList:
    def __init__(self, parent: tk.Frame, theme: dict, on_copy=None, on_delete=None, on_select=None):
        self.parent = parent
        self.theme = theme
        self.on_copy = on_copy
        self.on_delete = on_delete
        self.on_select = on_select
        self._bubbles: List[MessageBubble] = []

    def clear(self):
        for b in self._bubbles:
            try:
                b.destroy()
            except Exception:
                pass
        self._bubbles = []

    def show_messages(self, messages: List[Dict[str, str]]):
        # render given messages; set indices
        self.clear()
        for idx, m in enumerate(messages):
            role = m.get('role', 'assistant')
            content = m.get('content', '')
            b = MessageBubble(self.parent, role, content, self.theme, on_copy=self._on_copy, on_delete=lambda i=idx: self._on_delete(i), on_select=self._on_select)
            b.set_index(idx)
            b.pack(fill='x', pady=6, padx=0, anchor='w' if role!='user' else 'e')
            self._bubbles.append(b)

    def append_message(self, role: str, content: str):
        idx = len(self._bubbles)
        b = MessageBubble(self.parent, role, content, self.theme, on_copy=self._on_copy, on_delete=lambda i=idx: self._on_delete(i), on_select=self._on_select)
        b.set_index(idx)
        b.pack(fill='x', pady=6, padx=0, anchor='w' if role!='user' else 'e')
        self._bubbles.append(b)
        return b

    def _on_copy(self, text: str):
        # For individual copy actions, show a simple confirmation instead of the content
        if self.on_copy:
            try:
                self.on_copy('已复制 √')
            except Exception:
                pass

    def _on_select(self, idx: int, selected: bool):
        if self.on_select:
            try:
                self.on_select(idx, selected)
            except Exception:
                pass

    def _on_delete(self, idx: int):
        # call external hook if provided; default removes and refreshes indices
        if self.on_delete:
            try:
                self.on_delete(idx)
            except Exception:
                pass
        else:
            # internal delete
            try:
                if 0 <= idx < len(self._bubbles):
                    self._bubbles[idx].destroy()
                    del self._bubbles[idx]
                    # reindex remaining
                    for i,b in enumerate(self._bubbles):
                        b.set_index(i)
            except Exception:
                pass

    def get_bubbles(self):
        return list(self._bubbles)

    def set_theme(self, theme: dict):
        self.theme = theme
        # re-render not implemented here
