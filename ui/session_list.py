import tkinter as tk
from typing import Callable, Optional, List, Dict

class SessionList:
    """封装会话列表与右键菜单功能"""
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.frame = tk.Frame(parent)
        self.listbox = tk.Listbox(self.frame, width=30)
        self.listbox.pack(side='left', fill='y')
        # current theme (optional)
        self._theme = None
        self._session_ids: List[str] = []

        self.menu = tk.Menu(self.frame, tearoff=0)
        self.menu.add_command(label="重命名", command=self._on_rename)
        self.menu.add_command(label="删除", command=self._on_delete)
        self.menu.add_separator()
        self.menu.add_command(label="导出为 TXT", command=lambda: self._on_export('txt'))
        self.menu.add_command(label="导出为 Markdown", command=lambda: self._on_export('md'))
        self.menu.add_command(label="导出为 JSON", command=lambda: self._on_export('json'))
        self.listbox.bind('<Button-3>', self._show_menu)

        # callbacks
        self.on_select: Optional[Callable[[str], None]] = None
        self.on_rename: Optional[Callable[[str], None]] = None
        self.on_delete: Optional[Callable[[str], None]] = None
        self.on_export: Optional[Callable[[str, str], None]] = None

        self.listbox.bind('<<ListboxSelect>>', self._handle_select)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def set_sessions(self, sessions: List[Dict[str, str]]):
        self.listbox.delete(0, tk.END)
        self._session_ids = []
        for s in sessions:
            title = s.get('title', '')
            # sessions use 'session_id' as key
            sid = s.get('session_id') or s.get('id')
            self._session_ids.append(sid)
            self.listbox.insert(tk.END, title)

    def _handle_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._session_ids) and self.on_select:
            try:
                self.on_select(self._session_ids[idx])
            except Exception:
                pass

    def set_theme(self, theme: dict):
        """Apply theme colors to the session list (so selected row matches theme)."""
        self._theme = theme
        try:
            # background and foreground
            self.listbox.config(bg=theme.get('bg'), fg=theme.get('text'), selectforeground=theme.get('text'))
        except Exception:
            pass
        try:
            # selection highlight for history rows
            sel_bg = theme.get('history_selected') if theme.get('history_selected') else theme.get('accent')
            self.listbox.config(selectbackground=sel_bg)
        except Exception:
            pass

    def _show_menu(self, event):
        try:
            # select under cursor
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.listbox.nearest(event.y))
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                self.menu.grab_release()
            except Exception:
                pass

    def _on_rename(self):
        sid = self._get_selected()
        if sid and self.on_rename:
            try:
                self.on_rename(sid)
            except Exception:
                pass

    def _on_delete(self):
        sid = self._get_selected()
        if sid and self.on_delete:
            try:
                self.on_delete(sid)
            except Exception:
                pass

    def _on_export(self, format_type: str):
        sid = self._get_selected()
        if sid and self.on_export:
            try:
                self.on_export(sid, format_type)
            except Exception:
                pass

    def _get_selected(self) -> Optional[str]:
        sel = self.listbox.curselection()
        if not sel:
            return None
        # prefer the most recently selected index (last in the selection tuple)
        idx = sel[-1]
        if idx < len(self._session_ids):
            return self._session_ids[idx]
        return None
