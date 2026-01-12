"""基于 Tkinter 的简单图形界面。"""
import tkinter as tk
from tkinter import scrolledtext, simpledialog, ttk, messagebox
from typing import Any, List, Dict
import queue
from .theme import get_theme
import datetime
import tkinter.font as tkfont
import textwrap

# helpers
from .notifications import show_notification
import config


class AppUI:
    PROVIDERS = {
        "": "选择API服务商",
        "gemini": "Google Gemini",
        "siliconflow": "硅基流动",
        "deepseek": "DeepSeek",
        "grok": "Grok (xAI)"
    }

    def __init__(self, controller: Any):
        self.c = controller
        self.root = tk.Tk()
        self.root.title("LLM Demo")

        # 主题（默认使用配置中设置）
        self._theme_name = getattr(self.c, 'cfg', {}).get('theme', 'light') if self.c else 'light'
        self._theme = get_theme(self._theme_name)

        # 选中消息索引集合（基于当前 session 的消息索引）
        self._selected_msg_indices: set = set()

        # 通知标签（用于短时提示），初始不显示，后续用 show_notification 居中显示
        self._notif_var = tk.StringVar()
        self._notif_label = tk.Label(self.root, textvariable=self._notif_var, fg=self._theme.get('text'), bg=self._theme.get('accent'), padx=10, pady=4)
        self._notif_label.place_forget()

        # 默认最大输入行数扩展
        self._input_max_lines = 30

        # 顶部配置面板（拆分到独立模块）
        from .config_panel import ConfigPanel
        current_config = getattr(self.c, 'cfg', {}) if self.c else {}
        self._config_panel = ConfigPanel(self.root, self._theme, current_config)
        self._config_panel.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        # wire callbacks
        self._config_panel.on_save = lambda cfg: self.handle_save_config(cfg)
        self._config_panel.on_test = lambda: self.handle_test_connection()
        self._config_panel.on_toggle_theme = self._toggle_theme
        self._config_panel.on_copy_selected = self.handle_copy_selected
        self._config_panel.on_delete_selected = self.handle_delete_selected
        self._config_panel.on_export_selected = self.handle_export_selected
        self._config_panel.on_model_changed = self.handle_model_changed
        self._config_panel.on_history_changed = lambda count: self.c.on_update_history_messages(count) if self.c else None
        self._config_panel.on_manage_prompt = lambda: self.c.on_manage_prompt() if self.c else None
        # initial batch buttons disabled
        self._config_panel.set_batch_buttons_enabled(False)
        # compatibility
        self.copy_sel_btn = self._config_panel.copy_sel_btn
        self.del_sel_btn = self._config_panel.del_sel_btn
        self.export_sel_btn = self._config_panel.export_sel_btn

        # 左侧会话列表（拆分到独立模块）
        from .session_list import SessionList
        self._session_list = SessionList(self.root)
        self._session_list.grid(row=1, column=0, rowspan=4, sticky="ns")
        self._session_list.on_select = lambda sid: self.c.on_select_session(sid) if self.c else None
        self._session_list.on_rename = lambda sid: self.handle_rename_session(sid)
        self._session_list.on_delete = lambda sid: self.handle_delete_session(sid)
        self._session_list.on_export = lambda sid, fmt: self.handle_export_session(fmt, sid)
        # compatibility
        self.session_listbox = self._session_list.listbox
        self.session_menu = self._session_list.menu

        # 右侧对话显示（消息气泡容器）
        self.msg_container = tk.Frame(self.root, bg=self._theme.get('bg'))
        self.msg_container.grid(row=1, column=1, columnspan=3, sticky="nsew")

        self.msg_canvas = tk.Canvas(self.msg_container, borderwidth=0, highlightthickness=0, bg=self._theme.get('bg'))
        self.msg_scroll = ttk.Scrollbar(self.msg_container, orient="vertical", command=self.msg_canvas.yview)
        self.msg_inner = tk.Frame(self.msg_canvas, bg=self._theme.get('bg'))
        self.msg_inner_id = self.msg_canvas.create_window((0, 0), window=self.msg_inner, anchor="nw")

        # MessageList 管理消息渲染（拆分到独立模块）
        try:
            from .message_renderer import MessageList
            self._message_list = MessageList(self.msg_inner, self._theme, on_copy=self._show_notification, on_delete=self._on_bubble_delete, on_select=self._on_bubble_select)
        except Exception:
            self._message_list = None

        self.msg_canvas.configure(yscrollcommand=self.msg_scroll.set)
        self.msg_canvas.pack(side="left", fill="both", expand=True)
        self.msg_scroll.pack(side="right", fill="y")
        # 主布局自适应：使消息区和输入随窗口调整大小
        try:
            self.root.grid_rowconfigure(1, weight=1)
            self.root.grid_columnconfigure(1, weight=1)
        except Exception:
            pass

        # 自动调整滚动区域
        self.msg_inner.bind("<Configure>", lambda e: self.msg_canvas.configure(scrollregion=self.msg_canvas.bbox("all")))
        self.msg_canvas.bind("<Configure>", self._on_msg_canvas_configure)
        self.msg_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 临时气泡引用（用于"正在思考..."）
        self._temp_bubble = None
        # 输入区已拆分到 InputArea 模块
        # 相关控件与回调由 InputArea 管理，保留兼容属性以供旧代码使用
        self._input_min_lines = 2
        self._input_max_lines = 10
        self._placeholder_text = ''

        # 使用 InputArea（如果可用）管理输入区
        try:
            from .input_area import InputArea
            self._input_area = InputArea(self.root, self._theme, default_height=4)
            self._input_area.grid(row=2, column=1, columnspan=3, sticky='ew')
            self._input_area.on_send = lambda text: self.c.on_send(text) if self.c else None
            self._input_area.on_new_session = self.handle_new_session
            # 兼容老属性
            self.input_text = self._input_area.input_text
            self._resizer = self._input_area.resizer
            self.send_btn = self._input_area.send_btn
            self.new_btn = self._input_area.new_btn
        except Exception:
            default_input_height = 4
            self.input_text = scrolledtext.ScrolledText(self.root, width=70, height=default_input_height, wrap=tk.WORD)
            self.input_text.grid(row=3, column=1, sticky="ew")
            self.input_text.bind('<KeyRelease>', self._auto_expand_input)
            self.input_text.bind("<Control-Return>", self._handle_send_event)
            self.input_text.bind("<Command-Return>", self._handle_send_event)
            self._set_placeholder('输入消息，Ctrl+Enter 发送...')
            send_btn = tk.Button(self.root, text="发送", command=self.handle_send)
            send_btn.grid(row=3, column=2, sticky="w")
            new_btn = tk.Button(self.root, text="新建会话", command=self.handle_new_session)
            new_btn.grid(row=4, column=1, sticky="w")        # Apply theme to components
        try:
            # prefer modular set_theme methods if available
            try:
                if getattr(self, '_input_area', None):
                    self._input_area.set_theme(self._theme)
                else:
                    btn_bg = self._theme.get('accent')
                    btn_fg = 'white' if self._theme_name=='light' else 'black'
                    try:
                        send_btn.config(bg=btn_bg, fg=btn_fg)
                    except Exception:
                        pass
                    try:
                        new_btn.config(bg=btn_bg, fg=btn_fg)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                self._config_panel.set_theme(self._theme)
            except Exception:
                pass
            try:
                self.theme_btn.config(bg=self._theme.get('bg'), fg=self._theme.get('text'))
            except Exception:
                pass
        except Exception:
            pass

        # 拖拽相关状态
        self._resizing = False
        self._resize_start_y = 0
        self._orig_input_px = 0
        self._font = tkfont.Font(font=self.input_text['font'])

    def _on_msg_canvas_configure(self, event):
        # 保持内框宽度与画布一致以便换行
        canvas_width = event.width
        self.msg_canvas.itemconfig(self.msg_inner_id, width=canvas_width)
        # 延迟重绘以在调整大小时重新计算气泡换行（防抖）
        try:
            if getattr(self, '_rerender_job', None):
                self.root.after_cancel(self._rerender_job)
        except Exception:
            pass
        self._rerender_job = self.root.after(200, self._rerender_messages)
        # 更新背景颜色
        try:
            self.msg_canvas.config(bg=self._theme.get('bg'))
            self.msg_inner.config(bg=self._theme.get('bg'))
        except Exception:
            pass

    def _on_mousewheel(self, event):
        # 支持滚轮滚动
        # 在Windows上 event.delta 是120的倍数
        try:
            self.msg_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _slide_in(self, widget: tk.Widget, anchor: str = 'w', steps: int = 6):
        """简单的滑入动画：从水平偏移移动到目标位置。"""
        try:
            widget.update_idletasks()
            w = widget.winfo_width()
            # 初始偏移
            offset = 20 if anchor == 'w' else -20
            def step(i):
                try:
                    widget.place_configure(x=offset*(steps-i)//steps)
                except Exception:
                    pass
                if i < steps:
                    widget.after(20, lambda: step(i+1))
                else:
                    try:
                        widget.place_forget()
                    except Exception:
                        pass
            # 使用 place 临时调整位置
            widget.place(relx=0.0, rely=0.0, x=offset)
            step(0)
        except Exception:
            pass

    def _rerender_messages(self):
        """在调整大小后重新渲染所有消息以重新换行"""
        self._rerender_job = None
        msgs = getattr(self, '_last_messages', None)
        if not msgs:
            return
        # 重新渲染
        self.clear_messages()
        for m in msgs:
            role = m.get('role', 'assistant')
            content = m.get('content', '')
            self.add_message_bubble(role, content)
        # 重新应用主题背景
        try:
            self.msg_canvas.config(bg=self._theme.get('bg'))
            self.msg_inner.config(bg=self._theme.get('bg'))
        except Exception:
            pass

    def _draw_round_rect(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, r: float = 8, **kwargs):
        """在指定的 canvas 上绘制圆角矩形（返回绘制的对象id）"""
        # 中心矩形
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs)
        # 四个圆角（作为填充饼片）
        canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style='pieslice', **kwargs)
        canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style='pieslice', **kwargs)
        canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style='pieslice', **kwargs)
        canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style='pieslice', **kwargs)

    # ---------- 拖拽调整输入区高度的方法 ----------
    def _start_resize(self, event):
        self._resizing = True
        self._resize_start_y = event.y_root
        try:
            # 以行数为单位存储原始高度，更稳定
            self._orig_input_lines = int(self.input_text['height'])
        except Exception:
            self._orig_input_lines = 4

    def _do_resize(self, event):
        if not self._resizing:
            return
        try:
            line_px = max(8, getattr(self, '_font').metrics('linespace'))
        except Exception:
            line_px = 16
        # 计算像素差并转换为行数偏移：上拉（y_root 减小）应当增加行数
        delta_pixels = self._resize_start_y - event.y_root
        delta_lines = int(round(delta_pixels / line_px))
        new_lines = max(self._input_min_lines, min(self._input_max_lines, self._orig_input_lines + delta_lines))
        try:
            self.input_text.config(height=new_lines)
        except Exception:
            pass

    def _end_resize(self, event):
        self._resizing = False
        # 将调整后的高度持久化
        try:
            rows = int(self.input_text['height'])
            if self.c:
                self.c.on_update_config({"input_height": rows})
        except Exception:
            pass

    def add_message_bubble(self, role: str, content: str, temporary: bool = False):
        """兼容层：使用 MessageList 添加消息气泡（优先使用新模块）。"""
        if self._message_list:
            try:
                b = self._message_list.append_message(role, content)
                if temporary:
                    try:
                        if self._temp_bubble:
                            try:
                                self._temp_bubble.destroy()
                            except Exception:
                                pass
                        self._temp_bubble = b.widget()
                    except Exception:
                        pass
                # 自动滚动到底部
                try:
                    self.root.after(50, lambda: self.msg_canvas.yview_moveto(1.0))
                except Exception:
                    pass
                return b.widget()
            except Exception:
                pass
        # 兜底：未能使用 MessageList 时返回 None
        return None

    def remove_temp_bubble(self):
        if self._temp_bubble:
            try:
                self._temp_bubble.destroy()
            except Exception:
                pass
            self._temp_bubble = None

    def clear_messages(self):
        for w in list(self.msg_inner.winfo_children()):
            try:
                w.destroy()
            except Exception:
                pass

    def show_messages(self, messages: List[Dict[str, str]]):
        # 记录消息用于 resize 时重绘
        self._last_messages = messages
        # 委托 MessageList 渲染
        if self._message_list:
            try:
                self._message_list.show_messages(messages)
                # 清除先前的选中状态（重新渲染后索引可能变化）
                try:
                    self._selected_msg_indices.clear()
                    self.copy_sel_btn.config(state='disabled')
                    self.del_sel_btn.config(state='disabled')
                    self.export_sel_btn.config(state='disabled')
                except Exception:
                    pass
                # 自动滚动到底部
                try:
                    self.root.after(100, lambda: self.msg_canvas.yview_moveto(1.0))
                except Exception:
                    pass
                return
            except Exception:
                pass
        # 兜底：逐条渲染（兼容旧逻辑）
        self.clear_messages()
        for idx, m in enumerate(messages):
            role = m.get('role', '?')
            content = m.get('content', '')
            if role not in ('user', 'assistant'):
                role = 'assistant'
            bubble = self.add_message_bubble(role, content)
            try:
                bubble._msg_index = idx
            except Exception:
                pass

        # 布局权重
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # 注意：不要在这里重置会话映射或重新绑定 Listbox 事件，
        # 这些操作应在 refresh_sessions 中完成以保持会话映射一致。
        # 保持 show_messages 只负责渲染消息内容。

    def refresh_sessions(self, sessions: List[Dict[str, str]]):
        # refresh sessions called
        # use the new SessionList implementation
        self._session_list.set_sessions(sessions)
        # keep _session_ids for backward compatibility
        self._session_ids = [s.get('session_id') for s in sessions]
        # auto-select controller current session
        if self.c and getattr(self.c, 'current_session', None):
            cur = self.c.current_session
            if cur in self._session_ids:
                idx = self._session_ids.index(cur)
                try:
                    self.session_listbox.selection_clear(0, tk.END)
                    self.session_listbox.selection_set(idx)
                    self.handle_select(None)
                except Exception:
                    pass


    def handle_send(self):
        if getattr(self, '_input_area', None):
            prompt = self._input_area.get_text()
        else:
            prompt = self.input_text.get("1.0", tk.END).strip()
        if not prompt:
            return
        if self.c:
            self.c.on_send(prompt)
        if getattr(self, '_input_area', None):
            self._input_area.clear()
        else:
            self.input_text.delete("1.0", tk.END)

    def _on_bubble_delete(self, idx: int):
        """回调：消息气泡请求删除指定索引的消息。"""
        try:
            if not self.c or not self.c.current_session:
                return
            self.c.on_delete_message(self.c.current_session, idx)
            # 刷新显示
            self.show_messages(self.c.storage.get_session(self.c.current_session).get('messages', []))
        except Exception:
            pass

    def _on_bubble_select(self, idx: int, selected: bool):
        """回调：单条消息被选中/取消选中。更新选中集合以及批量操作按钮状态。"""
        try:
            if selected:
                self._selected_msg_indices.add(idx)
            else:
                self._selected_msg_indices.discard(idx)
            enabled = bool(self._selected_msg_indices)
            # prefer high-level API on ConfigPanel if available
            try:
                if getattr(self, '_config_panel', None):
                    self._config_panel.set_batch_buttons_enabled(enabled)
                else:
                    state = 'normal' if enabled else 'disabled'
                    self.copy_sel_btn.config(state=state)
                    self.del_sel_btn.config(state=state)
                    self.export_sel_btn.config(state=state)
            except Exception:
                pass
        except Exception:
            pass

    def handle_new_session(self):
        title = simpledialog.askstring("New Session", "Session title:")
        if title and self.c:
            self.c.on_new_session(title)

    def handle_select(self, event):
        sel = self.session_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._session_ids) and self.c:
            sid = self._session_ids[idx]
            self.c.on_select_session(sid)

    def run(self):
        # 启动前刷新会话列表和配置
        if self.c:
            self.refresh_sessions(self.c.storage.list_sessions())
            self.load_config()
            # 关闭时保存窗口尺寸
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            # 启动队列检查循环
            self._check_result_queue()
        self.root.mainloop()

    def load_config(self):
        """加载配置到UI控件"""
        if not self.c:
            return
        try:
            current_config = getattr(self.c, 'cfg', {})
            # 加载配置面板的配置
            if hasattr(self, '_config_panel') and self._config_panel:
                self._config_panel.load_config(current_config)
        except Exception as e:
            print(f"加载配置失败: {e}")

    def _on_close(self):
        """在窗口关闭前保存窗口尺寸到配置并退出"""
        try:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            if self.c:
                self.c.on_update_config({"window_width": width, "window_height": height, "theme": self._theme_name})
        except Exception:
            pass
        self.root.destroy()

    def _check_result_queue(self):
        """定期检查结果队列，如果有结果则更新UI"""
        if self.c:
            try:
                # 非阻塞检查队列
                while True:
                    reply = self.c.result_queue.get_nowait()
                    # 处理结果：移除临时气泡并显示回复
                    self.remove_temp_bubble()
                    # 如果 reply 是 dict（包含 role/content/timestamp) 兼容旧版本
                    if isinstance(reply, dict):
                        role = reply.get('role', 'assistant')
                        content = reply.get('content', '')
                        self.add_message_bubble(role, content)
                        # 保存到 storage
                        if self.c and getattr(self.c, 'current_session', None):
                            self.c.storage.append_message(self.c.current_session, role, content)
                    else:
                        self._update_ui_with_reply(reply)
            except queue.Empty:
                # 队列为空，继续
                pass

        # 每100ms检查一次队列
        self.root.after(100, self._check_result_queue)

    def _show_notification(self, text: str, duration: int = 2000):
        """在 UI 中部短时显示通知（默认 2000ms）。"""
        try:
            self._notif_var.set(text)
            # 将 label 居中放置在消息容器上方的一点位置
            try:
                # small offset from top of message area
                self._notif_label.place(relx=0.5, rely=0.06, anchor='n')
                self._notif_label.lift()
                # 自动隐藏（先取消任何已安排的清除）
                self.root.after(duration, lambda: self._notif_label.place_forget())
            except Exception:
                # 失败时回退到设置变量且自动清空文本
                self.root.after(duration, lambda: self._notif_var.set(''))
        except Exception:
            pass

    def _update_ui_with_reply(self, reply: str):
        """在主线程中更新UI显示回复"""
        # 使用气泡渲染回复并保存
        try:
            self.add_message_bubble('assistant', reply)
        except Exception:
            # 如果气泡渲染失败，回退到完整渲染
            if self.c and self.c.current_session:
                self.show_messages(self.c.storage.get_session(self.c.current_session).get("messages", []) + [{'role':'assistant','content':reply}])

        # 保存回复到存储
        if self.c and self.c.current_session:
            self.c.storage.append_message(self.c.current_session, "assistant", reply)

        # 自动滚动到底部
        try:
            self.root.after(100, lambda: self.msg_canvas.yview_moveto(1.0))
        except Exception:
            pass

    def load_config(self):
        """加载配置到UI控件"""
        if not self.c:
            return
        cfg = self.c.cfg
        # Prefer new ConfigPanel if present
        try:
            if getattr(self, '_config_panel', None):
                try:
                    self._config_panel.provider_var.set(cfg.get('provider', ''))
                    self._config_panel.key_var.set(cfg.get('api_key', ''))
                    max_history = cfg.get('max_history_messages', 10)
                    if max_history <= 0:
                        self._config_panel.history_var.set('全部')
                    else:
                        self._config_panel.history_var.set(str(max_history))
                    self._config_panel.timeout_var.set(str(cfg.get('timeout', 60)))
                    self._config_panel.input_height_var.set(str(cfg.get('input_height', 4)))
                    # theme propagation
                    try:
                        self._config_panel.set_theme(self._theme)
                    except Exception:
                        pass
                except Exception:
                    pass
                # still apply theme to canvas
        except Exception:
            pass

        # 应用主题
        try:
            self._theme_name = cfg.get('theme', self._theme_name)
            self._theme = get_theme(self._theme_name)
            self.msg_canvas.config(bg=self._theme.get('bg'))
            self.msg_inner.config(bg=self._theme.get('bg'))
        except Exception:
            pass

        # Fallback: keep legacy vars working if ConfigPanel not present
        try:
            if not getattr(self, '_config_panel', None):
                max_history = cfg.get("max_history_messages", 10)
                if max_history <= 0:
                    self.history_var.set("全部")
                else:
                    self.history_var.set(str(max_history))

                # 加载超时设置
                timeout = cfg.get("timeout", 60)
                self.timeout_var.set(str(timeout))

                # 加载输入高度设置
                input_height = cfg.get("input_height", 4)
                self.input_height_var.set(str(input_height))
                if hasattr(self, 'input_text'):
                    try:
                        self.input_text.config(height=int(input_height))
                    except Exception:
                        pass
        except Exception:
            pass
        # 加载最大输入行数（可选）
        input_max_lines = cfg.get('input_max_lines', None)
        if input_max_lines is not None:
            try:
                self._input_max_lines = int(input_max_lines)
            except Exception:
                pass

        # 加载窗口大小（宽x高）并允许调整
        width = cfg.get("window_width", 1000)
        height = cfg.get("window_height", 700)
        try:
            self.root.geometry(f"{int(width)}x{int(height)}")
        except Exception:
            pass
        self.root.resizable(True, True)

    def handle_provider_change(self, event):
        """处理provider选择变化"""
        pass  # 可以在这里添加实时验证或提示

    def _toggle_theme(self):
        try:
            self._theme_name = 'dark' if self._theme_name == 'light' else 'light'
            self._theme = get_theme(self._theme_name)
            # 立即应用主题
            try:
                self.msg_canvas.config(bg=self._theme.get('bg'))
                self.msg_inner.config(bg=self._theme.get('bg'))
            except Exception:
                pass
            # propagate theme to other components
            try:
                if getattr(self, '_config_panel', None):
                    self._config_panel.set_theme(self._theme)
            except Exception:
                pass
            try:
                if getattr(self, '_session_list', None):
                    self._session_list.set_theme(self._theme)
            except Exception:
                pass
        except Exception:
            pass

    def handle_history_change(self, event):
        """处理历史消息数量变化"""
        if not self.c:
            return

        history_value = self.history_var.get()
        if history_value == "全部":
            new_count = 0  # 0表示全部
        else:
            try:
                new_count = int(history_value)
            except ValueError:
                return

        self.c.on_update_history_messages(new_count)

    def handle_timeout_change(self, event):
        """处理超时设置变化"""
        if not self.c:
            return

        timeout_value = self.timeout_var.get()
        try:
            timeout = int(timeout_value)
            self.c.on_update_timeout(timeout)
        except ValueError:
            return

    def handle_input_height_change(self, event):
        """处理输入高度变化"""
        if not self.c:
            return

        value = self.input_height_var.get()
        try:
            h = int(value)
            if hasattr(self, 'input_text'):
                self.input_text.config(height=h)
            # 持久化配置
            self.c.on_update_config({"input_height": h})
        except ValueError:
            return

    def _handle_send_event(self, event):
        """键盘事件处理：Ctrl+Enter 或 Command+Enter 发送"""
        self.handle_send()
        return "break"

    def _auto_expand_input(self, event=None):
        """根据行数自动扩展输入框高度（受 _input_min_lines/_input_max_lines 限制）"""
        try:
            content = self.input_text.get('1.0', 'end-1c')
            lines = content.count('\n') + 1
            lines = max(self._input_min_lines, min(self._input_max_lines, lines))
            self.input_text.config(height=lines)
        except Exception:
            pass

    def _set_placeholder(self, text: str):
        self._placeholder_text = text
        try:
            if not self.input_text.get('1.0', 'end-1c').strip():
                self.input_text.insert('1.0', text)
                self.input_text.tag_add('placeholder', '1.0', 'end')
                self.input_text.tag_config('placeholder', foreground=self._theme.get('muted'))
                def _clear_placeholder(evt):
                    self.input_text.delete('1.0', 'end')
                    # 移除占位绑定（无需传入函数对象，调用 unbind(sequence) 即可）
                    self.input_text.unbind('<FocusIn>')
                self.input_text.bind('<FocusIn>', _clear_placeholder)
        except Exception:
            pass

    def handle_save_config(self, cfg: dict | None = None):
        """保存配置；如果传入 cfg 则直接使用它（供 ConfigPanel 回调使用），否则回退到从旧控件读取。"""
        if not self.c:
            return
        if cfg is not None:
            # 自动保存模式，保存配置并显示反馈
            try:
                self.c.on_update_config(cfg)
                self._show_notification('已保存 √', duration=2000)
            except Exception:
                pass
            return

        # 手动保存模式，显示消息框
        try:
            # 这里可以添加手动保存的逻辑，如果需要的话
            self._show_notification('已保存 √', duration=2000)
        except Exception:
            pass

    def handle_test_connection(self):
        """测试连接：使用当前选择的模型"""
        try:
            import config
            current_model = config.get_current_model()
            if not current_model:
                tk.messagebox.showwarning("警告", "请先选择模型")
                return

            model_config = config.get_model(current_model)
            if not model_config:
                tk.messagebox.showerror("错误", "模型配置不存在")
                return

            from api import ApiClient
            # 创建临时配置用于测试
            temp_cfg = {
                'provider': 'custom',
                'base_url': model_config['base_url'],
                'api_key': model_config['api_key'],
                'model': model_config['model']
            }
            client = ApiClient(temp_cfg)
            reply = client.call_model("Hello, test connection!")
            tk.messagebox.showinfo("测试成功", f"回复: {reply[:100]}...")
        except Exception as e:
            tk.messagebox.showerror("测试失败", f"错误: {str(e)}")

    def handle_model_changed(self, model_name: str):
        """处理模型选择变化"""
        try:
            config.set_current_model(model_name)
            # 可以在这里更新UI显示或其他逻辑
            print(f"当前模型已切换为: {model_name}")
        except Exception as e:
            print(f"切换模型失败: {e}")

    # ---------- 批量消息操作 ----------
    def handle_copy_selected(self):
        """复制选中消息的内容并显示提示"""
        if not self.c or not self.c.current_session:
            return
        if not self._selected_msg_indices:
            return
        sess = self.c.storage.get_session(self.c.current_session)
        msgs = sess.get('messages', [])
        contents = [msgs[i].get('content','') for i in sorted(self._selected_msg_indices) if 0<=i<len(msgs)]
        if not contents:
            return
        text = '\n\n'.join(contents)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._show_notification('已复制 √', duration=2000)
        except Exception:
            pass

    def handle_delete_selected(self):
        """删除选中消息（批量）"""
        if not self.c or not self.c.current_session:
            return
        if not self._selected_msg_indices:
            return
        if not messagebox.askyesno('确认', '删除所选消息？'):
            return
        indices = sorted(list(self._selected_msg_indices))
        self.c.on_delete_messages(self.c.current_session, indices)
        self._selected_msg_indices.clear()

    def handle_export_selected(self):
        """导出选中消息（批量）"""
        if not self.c or not self.c.current_session:
            return
        if not self._selected_msg_indices:
            return
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(title='导出所选消息', defaultextension='.txt', filetypes=[('Text files','*.txt'),('All files','*.*')])
        if not filename:
            return
        indices = sorted(list(self._selected_msg_indices))
        # 默认导出为 txt
        self.c.on_export_messages(self.c.current_session, indices, filename, format_type='txt')
        self._show_notification('已导出 √', duration=2000)

    def handle_test_connection(self):
        """测试API连接"""
        if not self.c:
            return
        provider = self.provider_var.get()
        api_key = self.key_var.get().strip()
        if not provider or not api_key:
            tk.messagebox.showwarning("警告", "请先选择服务商并输入API Key")
            return

        # 创建临时客户端进行测试
        from api import ApiClient
        test_cfg = {"provider": provider, "api_key": api_key, "timeout": 30}
        client = ApiClient(test_cfg)

        try:
            reply = client.call_model("Hello, this is a test message")
            if reply.startswith("[ERROR]"):
                tk.messagebox.showerror("连接失败", f"API调用失败:\n{reply}")
            else:
                tk.messagebox.showinfo("连接成功", f"API响应:\n{reply[:100]}...")
        except Exception as e:
            tk.messagebox.showerror("连接失败", f"测试失败:\n{str(e)}")

    def show_session_menu(self, event):
        """显示会话右键菜单"""
        try:
            self.session_listbox.selection_clear(0, tk.END)
            self.session_listbox.selection_set(self.session_listbox.nearest(event.y))
            self.session_menu.post(event.x_root, event.y_root)
        except:
            pass

    def handle_rename_session(self, sid: str | None = None):
        """重命名会话，支持直接传入 sid 或使用当前列表选择项"""
        if not self.c:
            return
        if sid is None:
            sel = self.session_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            if idx >= len(self._session_ids):
                return
            session_id = self._session_ids[idx]
            current_name = self.session_listbox.get(idx).split(" - ")[0]
        else:
            session_id = sid
            # try to get current name from mapping
            idx = None
            try:
                idx = self._session_ids.index(session_id)
            except Exception:
                idx = None
            current_name = self.session_listbox.get(idx).split(" - ")[0] if idx is not None else ''

        new_name = simpledialog.askstring("重命名会话", "新名称:", initialvalue=current_name)
        if new_name and new_name.strip():
            self.c.on_rename_session(session_id, new_name.strip())

    def handle_delete_session(self, sid: str | None = None):
        """删除会话，支持传入 sid 或使用当前选择项"""
        if not self.c:
            return
        if sid is None:
            sel = self.session_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            if idx >= len(self._session_ids):
                return
            session_id = self._session_ids[idx]
            session_name = self.session_listbox.get(idx).split(" - ")[0]
        else:
            session_id = sid
            session_name = ''
        if messagebox.askyesno("确认删除", f"确定要删除会话 '{session_name}' 吗？\n此操作不可撤销。"):
            self.c.on_delete_session(session_id)

    def handle_export_session(self, format_type, sid: str | None = None):
        """导出会话，支持传入 sid 或使用当前选择项"""
        if not self.c:
            return
        if sid is None:
            sel = self.session_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            if idx >= len(self._session_ids):
                return
            session_id = self._session_ids[idx]
            session_name = self.session_listbox.get(idx).split(" - ")[0]
        else:
            session_id = sid
            session_name = ''

        from tkinter import filedialog
        file_types = {
            "txt": [("Text files", "*.txt"), ("All files", "*.*")],
            "md": [("Markdown files", "*.md"), ("All files", "*.*")],
            "json": [("JSON files", "*.json"), ("All files", "*.*")]
        }

        filename = filedialog.asksaveasfilename(
            title=f"导出会话 - {format_type.upper()}",
            defaultextension=f".{format_type}",
            filetypes=file_types[format_type],
            initialfile=f"{session_name}.{format_type}" if session_name else None
        )

        if filename:
            self.c.on_export_session(session_id, filename, format_type)

__all__ = ["AppUI"]
