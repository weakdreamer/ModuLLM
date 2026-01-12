import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Callable, Optional

class InputArea:
    def __init__(self, parent: tk.Widget, theme: dict, default_height: int = 4):
        self.parent = parent
        self.theme = theme
        self.frame = tk.Frame(parent)
        self._build(default_height)
        # callbacks
        self.on_send: Optional[Callable[[str], None]] = None
        self.on_new_session: Optional[Callable[[], None]] = None

        # internal state for resize
        self._resizing = False
        self._resize_start_y = 0
        self._orig_input_lines = default_height

    def _build(self, default_height: int):
        # resizer frame
        self.resizer = tk.Frame(self.frame, height=6, cursor='sb_v_double_arrow', bg='#e0e0e0')
        self.resizer.pack(fill='x')
        self.resizer.bind('<Button-1>', self._start_resize)
        self.resizer.bind('<B1-Motion>', self._do_resize)
        self.resizer.bind('<ButtonRelease-1>', self._end_resize)

        self.input_text = scrolledtext.ScrolledText(self.frame, width=70, height=default_height, wrap=tk.WORD)
        self.input_text.pack(fill='x')
        self.input_text.bind('<KeyRelease>', self._auto_expand_input)
        self.input_text.bind('<Control-Return>', self._handle_send_event)
        self.input_text.bind('<Command-Return>', self._handle_send_event)
        self._placeholder = '输入消息，Ctrl+Enter 发送...'
        # insert placeholder and bind focus behavior to clear it when the user focuses the input
        self._set_placeholder(self._placeholder)
        def _clear_placeholder_on_focus(evt=None):
            try:
                cur = self.input_text.get('1.0', 'end-1c')
                if cur == self._placeholder:
                    self.input_text.delete('1.0', 'end')
                    # unbind after clearing once
                    self.input_text.unbind('<FocusIn>')
            except Exception:
                pass
        self.input_text.bind('<FocusIn>', _clear_placeholder_on_focus)

        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(fill='x')
        # place new session on the left and send on the right
        self.new_btn = ttk.Button(btn_frame, text='新建会话', command=self._on_new_session, style='Secondary.Rounded.TButton')
        self.new_btn.pack(side='left')
        self.send_btn = ttk.Button(btn_frame, text='发送', command=self._on_send, style='Primary.Rounded.TButton')
        self.send_btn.pack(side='right')

    # public API
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def set_theme(self, theme: dict):
        # Configure styles for buttons
        try:
            from .button_style import configure_button_styles
            configure_button_styles(theme)
        except Exception:
            pass
        try:
            self.send_btn.configure(style='Primary.Rounded.TButton')
            self.new_btn.configure(style='Secondary.Rounded.TButton')
        except Exception:
            pass

    def get_text(self) -> str:
        try:
            cur = self.input_text.get('1.0', 'end-1c')
            if not cur:
                return ''
            # if placeholder present (either alone or appended), remove it
            if self._placeholder and self._placeholder in cur:
                cur = cur.replace(self._placeholder, '')
            return cur.strip()
        except Exception:
            return ''

    def clear(self):
        self.input_text.delete('1.0', tk.END)

    def set_height(self, rows: int):
        try:
            self.input_text.config(height=rows)
        except Exception:
            pass

    def focus(self):
        try:
            self.input_text.focus_set()
        except Exception:
            pass

    # internals
    def _set_placeholder(self, text: str):
        self.input_text.insert('1.0', text)

    def _handle_send_event(self, event=None):
        self._on_send()
        return 'break'

    def _on_send(self):
        text = self.get_text()
        if not text:
            return
        if self.on_send:
            try:
                self.on_send(text)
            except Exception:
                pass
        self.clear()

    def _on_new_session(self):
        if self.on_new_session:
            try:
                self.on_new_session()
            except Exception:
                pass

    def _auto_expand_input(self, event=None):
        try:
            lines = int(self.input_text.index('end-1c').split('.')[0])
            new_h = max(2, min(30, lines))
            self.input_text.config(height=new_h)
        except Exception:
            pass

    def _start_resize(self, event):
        self._resizing = True
        self._resize_start_y = event.y_root
        try:
            self._orig_input_lines = int(self.input_text['height'])
        except Exception:
            self._orig_input_lines = 4

    def _do_resize(self, event):
        if not self._resizing:
            return
        try:
            # use simple pixel->lines heuristic
            line_px = 16
            delta_pixels = self._resize_start_y - event.y_root
            delta_lines = int(round(delta_pixels / line_px))
            new_lines = max(2, min(30, self._orig_input_lines + delta_lines))
            self.input_text.config(height=new_lines)
        except Exception:
            pass

    def _end_resize(self, event):
        self._resizing = False
