"""Message bubble widget encapsulation."""
import tkinter as tk
from typing import Any, Callable
import tkinter.font as tkfont
import datetime
import textwrap
from .selection import create_selection_rect


class MessageBubble:
    def __init__(self, parent: tk.Frame, role: str, content: str, theme: dict, on_copy: Callable | None = None, on_delete: Callable | None = None, on_select: Callable | None = None):
        self.parent = parent
        self.role = role
        self.content = content
        self.theme = theme
        self.on_copy = on_copy
        self.on_delete = on_delete
        self.on_select = on_select

        self.canvas = tk.Canvas(self.parent, bg=self.parent.cget('bg'), highlightthickness=0)
        self._msg_index = None
        self._sel_rect = None
        self._sel_hit = None
        self._selected = False

        self._render()

    def _render(self):
        content = self.content if isinstance(self.content, str) else str(self.content)
        content = content.encode('utf-8', errors='replace').decode('utf-8')

        pad_x = self.theme.get('padding_x', 12)
        pad_y = self.theme.get('padding_y', 8)

        # simple markdown code block support
        parts = []
        if '```' in content:
            segments = content.split('```')
            for i, seg in enumerate(segments):
                typ = 'code' if i % 2 == 1 else 'text'
                parts.append((typ, seg))
        else:
            parts.append(('text', content))

        canvas_w = max(300, self.parent.winfo_width() or 800)
        max_text_w = int(canvas_w * 0.65)

        font_normal = tkfont.Font(family='Helvetica', size=10)
        font_mono = tkfont.Font(family='Courier', size=9)

        y_cursor = pad_y

        # avatar placement
        avatar_r = 12
        avatar_x = 30
        avatar_y = avatar_r + 4
        avatar_fill = self.theme.get('accent') if self.role == 'user' else self.theme.get('muted')
        self.canvas.create_oval(avatar_x, avatar_y - avatar_r, avatar_x + avatar_r * 2, avatar_y + avatar_r, fill=avatar_fill, outline='')
        initial = 'U' if self.role == 'user' else 'A'
        self.canvas.create_text(avatar_x + avatar_r, avatar_y, text=initial, fill='white', font=font_normal)
        # selection checkbox (visible rect + larger hit area)
        try:
            sel_x = avatar_x - 22
            sel_y = avatar_y
            self._sel_rect, self._sel_hit = create_selection_rect(self.canvas, sel_x, sel_y, 12, fill='', outline=self.theme.get('muted'), callback=self._toggle_selection)
            # initialize visual state (unselected)
            try:
                self.set_selected(False)
            except Exception:
                pass
        except Exception:
            self._sel_rect = None
            self._sel_hit = None

        text_x = avatar_x + avatar_r * 2 + 6
        items = []
        for typ, txt in parts:
            if typ == 'text':
                wrapped = textwrap.fill(txt.strip(), width=80)
                tid = self.canvas.create_text(text_x, y_cursor, anchor='nw', text=wrapped, width=max_text_w - text_x, fill=self.theme.get('text'), font=font_normal)
                self.canvas.update_idletasks()
                bb = self.canvas.bbox(tid) or (0, 0, 0, 0)
                y_cursor = bb[3] + 6
                items.append(tid)
            else:
                code_lines = txt.strip('\n')
                if not code_lines:
                    continue
                code_tid = self.canvas.create_text(text_x, y_cursor, anchor='nw', text=code_lines, width=max_text_w - text_x, fill=self.theme.get('text'), font=font_mono)
                self.canvas.update_idletasks()
                bb = self.canvas.bbox(code_tid) or (0, 0, 0, 0)
                # background for code
                bg = '#f7f7f7' if self.theme.get('bg', '').lower() != '#1e1e1e' else '#2a2a2a'
                self.canvas.create_rectangle(bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4, fill=bg, outline='')
                self.canvas.tag_lower(code_tid)
                y_cursor = bb[3] + 6
                items.append(code_tid)

        ts = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')
        ts_id = self.canvas.create_text(canvas_w - pad_x - 80, y_cursor, anchor='se', text=ts, fill=self.theme.get('muted'), font=('Helvetica', 8))
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox(items[-1] if items else ts_id) or (0, 0, 0, 0)
        x1, y1, x2, y2 = bbox
        x2 += pad_x
        y2 += pad_y

        fill_color = self.theme.get('msg_bg_user') if self.role == 'user' else self.theme.get('msg_bg_assistant')
        r = self.theme.get('bubble_radius', 10)
        # draw rounded rect
        self._draw_round_rect(self.canvas, x1 - pad_x / 2, y1 - pad_y / 2, x2 + pad_x / 2, y2 + pad_y / 2, r, fill=fill_color, outline='')
        # raise text
        try:
            for it in items + [ts_id]:
                self.canvas.tag_raise(it)
        except Exception:
            pass

        # ensure selection checkbox is visible above the bubble background
        try:
            if getattr(self, '_sel_rect', None):
                self.canvas.tag_raise(self._sel_rect)
            if getattr(self, '_sel_hit', None):
                self.canvas.tag_raise(self._sel_hit)
        except Exception:
            pass

        # copy/delete buttons
        try:
            btn_margin = pad_x
            btn_x = min(x2 + btn_margin, canvas_w - 60)
            copy_btn = tk.Button(self.canvas, text='复制', fg=self.theme.get('accent'), bd=0, cursor='hand2')
            del_btn = tk.Button(self.canvas, text='删除', fg='#c0392b', bd=0, cursor='hand2')
            try:
                self.canvas.create_window(btn_x, y1 - pad_y / 2, anchor='nw', window=copy_btn)
                self.canvas.create_window(btn_x + 40, y1 - pad_y / 2, anchor='nw', window=del_btn)
            except Exception:
                copy_id = self.canvas.create_text(btn_x, y1 - pad_y / 2, anchor='nw', text='复制', fill=self.theme.get('accent'), font=('Helvetica', 9, 'underline'))
                del_id = self.canvas.create_text(btn_x + 40, y1 - pad_y / 2, anchor='nw', text='删除', fill='#c0392b', font=('Helvetica', 9, 'underline'))

            def _on_copy_widget(evt=None, text=self.content):
                try:
                    self.canvas.clipboard_clear()
                    self.canvas.clipboard_append(text)
                    if self.on_copy:
                        self.on_copy(text)
                except Exception:
                    pass

            def _on_delete_widget(evt=None):
                try:
                    if self.on_delete:
                        self.on_delete()
                except Exception:
                    pass

            try:
                copy_btn.bind('<Button-1>', _on_copy_widget)
                del_btn.bind('<Button-1>', _on_delete_widget)
            except Exception:
                try:
                    self.canvas.tag_bind(copy_id, '<Button-1>', lambda e: _on_copy_widget())
                    self.canvas.tag_bind(del_id, '<Button-1>', lambda e: _on_delete_widget())
                except Exception:
                    pass
        except Exception:
            pass

        # pack but set width to avoid place conflicts
        self.canvas.config(width=canvas_w, height=int(y2 + pad_y + 8))

    def set_index(self, idx: int):
        try:
            self._msg_index = idx
        except Exception:
            pass

    def set_selected(self, selected: bool):
        try:
            self._selected = selected
            if self._sel_rect:
                if selected:
                    # selected: use a dedicated contrast color (not equal to theme accent) + checkmark
                    sel_color = self.theme.get('selection') or self.theme.get('accent')
                    self.canvas.itemconfig(self._sel_rect, fill=sel_color, outline=sel_color, width=1)
                    try:
                        # ensure geometry is up-to-date before measuring
                        self.canvas.update_idletasks()
                        bbox = self.canvas.bbox(self._sel_rect) or (0,0,0,0)
                        cx = (bbox[0] + bbox[2]) / 2
                        cy = (bbox[1] + bbox[3]) / 2
                        if not getattr(self, '_sel_check', None):
                            self._sel_check = self.canvas.create_text(cx, cy, text='✓', fill='white', font=('Helvetica', 10, 'bold'))
                            # make the check clickable to toggle selection (avoid it blocking unselect)
                            try:
                                self.canvas.tag_bind(self._sel_check, '<Button-1>', lambda e: self._toggle_selection())
                                self.canvas.itemconfig(self._sel_check, cursor='hand2')
                            except Exception:
                                pass
                        else:
                            self.canvas.itemconfig(self._sel_check, text='✓', state='normal')
                            try:
                                self.canvas.tag_bind(self._sel_check, '<Button-1>', lambda e: self._toggle_selection())
                                self.canvas.itemconfig(self._sel_check, cursor='hand2')
                            except Exception:
                                pass
                        try:
                            self.canvas.tag_raise(self._sel_check)
                        except Exception:
                            pass
                        try:
                            # keep hit area above check so clicks are handled consistently
                            if getattr(self, '_sel_hit', None):
                                self.canvas.tag_raise(self._sel_hit)
                        except Exception:
                            pass
                    except Exception:
                        pass
                else:
                    # unselected: subtle fill and thicker muted border for contrast
                    try:
                        bg = self.theme.get('bg', '#ffffff')
                        default_fill = '#f0f0f0' if bg.startswith('#') and int(bg[1:3],16) > 0x80 else '#3a3a3a'
                    except Exception:
                        default_fill = '#f0f0f0'
                    self.canvas.itemconfig(self._sel_rect, fill=default_fill, outline=self.theme.get('muted'), width=2)
                    # remove checkmark if present
                    if getattr(self, '_sel_check', None):
                        try:
                            self.canvas.delete(self._sel_check)
                        except Exception:
                            pass
                        self._sel_check = None
                # make sure selection rect is on top
                try:
                    self.canvas.tag_raise(self._sel_rect)
                except Exception:
                    pass
                # force update to ensure visual changes are applied immediately
                try:
                    self.canvas.update()
                except Exception:
                    pass
        except Exception:
            pass

    def _toggle_selection(self):
        try:
            self._selected = not getattr(self, '_selected', False)
            # delegate visual update to set_selected to keep behavior consistent
            try:
                self.set_selected(self._selected)
            except Exception:
                pass
            if self.on_select and self._msg_index is not None:
                try:
                    self.on_select(self._msg_index, self._selected)
                except Exception:
                    pass
        except Exception:
            pass

    def pack(self, **kwargs: Any):
        self.canvas.pack(**kwargs)

    def destroy(self):
        try:
            self.canvas.destroy()
        except Exception:
            pass

    def _draw_round_rect(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, r: float = 8, **kwargs):
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs)
        canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style='pieslice', **kwargs)
        canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style='pieslice', **kwargs)
        canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style='pieslice', **kwargs)
        canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style='pieslice', **kwargs)

    # expose underlying widget for advanced operations
    def widget(self):
        return self.canvas
