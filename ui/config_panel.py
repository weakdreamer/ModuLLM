import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from .model_selection import ModelSelectionWindow
from .comm_settings import CommSettingsWindow

class ConfigPanel:
    """顶部配置面板：负责 provider/key/history/timeout/input_height/主题/批量操作按钮"""
    def __init__(self, parent: tk.Widget, theme: dict, current_config: dict = None):
        self.parent = parent
        self.theme = theme
        self.current_config = current_config or {}
        self.frame = tk.Frame(parent)
        self._build()
        # callbacks
        self.on_save: Optional[Callable[[dict], None]] = None
        self.on_test: Optional[Callable[[], None]] = None
        self.on_toggle_theme: Optional[Callable[[], None]] = None
        self.on_copy_selected: Optional[Callable[[], None]] = None
        self.on_delete_selected: Optional[Callable[[], None]] = None
        self.on_export_selected: Optional[Callable[[], None]] = None
        self.on_history_changed: Optional[Callable[[int], None]] = None
        self.on_manage_prompt: Optional[Callable[[], None]] = None
        self.on_comm_settings: Optional[Callable[[], None]] = None

    def _build(self):
        config_frame = tk.Frame(self.frame)
        config_frame.pack(fill='x', padx=5, pady=5)

        # Select Model button in top-left
        self.select_model_btn = ttk.Button(config_frame, text="选择模型", command=self._on_select_model, style='Primary.Rounded.TButton')
        self.select_model_btn.grid(row=0, column=0, sticky="w")

        tk.Label(config_frame, text="历史消息:").grid(row=0, column=1, sticky="w")
        self.history_var = tk.StringVar()
        self.history_combo = ttk.Combobox(config_frame, textvariable=self.history_var,
                                         values=["全部", "1", "2", "3", "5", "10", "15", "20", "30", "50"],
                                         width=8)
        self.history_combo.grid(row=0, column=2, sticky="w")
        self.history_combo.bind('<<ComboboxSelected>>', self._on_history_changed)
        self.history_combo.bind('<Return>', self._on_history_changed)

        tk.Label(config_frame, text="超时(秒):").grid(row=0, column=3, sticky="w")
        self.timeout_var = tk.StringVar()
        self.timeout_combo = ttk.Combobox(config_frame, textvariable=self.timeout_var,
                                         values=["30", "60", "90", "120", "180", "300"],
                                         state="readonly", width=8)
        self.timeout_combo.grid(row=0, column=4, sticky="w")
        self.timeout_combo.bind('<<ComboboxSelected>>', self._on_timeout_changed)

        # Use ttk Buttons with rounded styles for a modern look
        self.save_btn = ttk.Button(config_frame, text="保存配置", command=self._on_save, style='Primary.Rounded.TButton')
        self.save_btn.grid(row=0, column=5, padx=(5,0))

        self.theme_btn = ttk.Button(config_frame, text='切换主题', command=self._on_toggle_theme, style='Secondary.Rounded.TButton')
        self.theme_btn.grid(row=0, column=6, padx=(5,0))

        self.prompt_btn = ttk.Button(config_frame, text='管理Prompt', command=self._on_manage_prompt, style='Secondary.Rounded.TButton')
        self.prompt_btn.grid(row=0, column=7, padx=(5,0))

        # Communication settings button
        self.comm_btn = ttk.Button(config_frame, text='通信设置', command=self._on_comm_settings, style='Secondary.Rounded.TButton')
        self.comm_btn.grid(row=0, column=8, padx=(5,0))

        # Batch action buttons (use ttk for consistent rounded styling)
        self.copy_sel_btn = ttk.Button(config_frame, text='复制选中', command=self._on_copy_selected, style='Success.Rounded.TButton')
        self.copy_sel_btn.grid(row=0, column=9, padx=(5,0))
        self.del_sel_btn = ttk.Button(config_frame, text='删除选中', command=self._on_delete_selected, style='Danger.Rounded.TButton')
        self.del_sel_btn.grid(row=0, column=10, padx=(5,0))
        self.export_sel_btn = ttk.Button(config_frame, text='导出选中', command=self._on_export_selected, style='Primary.Rounded.TButton')
        self.export_sel_btn.grid(row=0, column=11, padx=(5,0))

    # public API
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def set_theme(self, theme: dict):
        self.theme = theme
        try:
            # configure ttk styles for rounded buttons
            try:
                from .button_style import configure_button_styles
                configure_button_styles(theme)
            except Exception:
                pass
            # apply simple colors where ttk doesn't apply
            try:
                self.theme_btn.config(bg=theme.get('bg'), fg=theme.get('text'))
            except Exception:
                pass
            # ensure save/test buttons use primary/secondary styles and color legacy batch buttons
            try:
                self.save_btn.configure(style='Primary.Rounded.TButton')
                self.test_btn.configure(style='Secondary.Rounded.TButton')
            except Exception:
                pass
            try:
                # color legacy tk Buttons for visibility
                self.copy_sel_btn.config(bg=theme.get('success', '#27ae60'), fg='white')
                self.del_sel_btn.config(bg=theme.get('danger', '#c0392b'), fg='white')
                self.export_sel_btn.config(bg=theme.get('accent', '#0078d4'), fg='white')
            except Exception:
                pass
        except Exception:
            pass

    def _on_save(self):
        if self.on_save:
            try:
                cfg = self.get_config()
                self.on_save(cfg)
            except Exception:
                pass

    def _on_test(self):
        if self.on_test:
            try:
                self.on_test()
            except Exception:
                pass

    def _on_select_model(self):
        """打开模型选择窗口"""
        try:
            window = ModelSelectionWindow(self.parent, self.theme)
            window.on_model_changed = self.on_model_changed
        except Exception as e:
            print(f"打开模型选择窗口失败: {e}")

    def _on_toggle_theme(self):
        if self.on_toggle_theme:
            try:
                self.on_toggle_theme()
            except Exception:
                pass

    def get_config(self):
        config = {}
        try:
            config["max_history_messages"] = int(self.history_var.get()) if self.history_var.get() and self.history_var.get() != "全部" else 0
        except ValueError:
            config["max_history_messages"] = 0
        try:
            config["timeout"] = int(self.timeout_var.get()) if self.timeout_var.get() else 30
        except ValueError:
            config["timeout"] = 30
        return config

    def _on_copy_selected(self):
        if self.on_copy_selected:
            try:
                self.on_copy_selected()
            except Exception:
                pass

    def _on_delete_selected(self):
        if self.on_delete_selected:
            try:
                self.on_delete_selected()
            except Exception:
                pass

    def _on_export_selected(self):
        if self.on_export_selected:
            try:
                self.on_export_selected()
            except Exception:
                pass

    def set_batch_buttons_enabled(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        try:
            self.copy_sel_btn.config(state=state)
            self.del_sel_btn.config(state=state)
            self.export_sel_btn.config(state=state)
        except Exception:
            pass

    def _on_history_changed(self, event=None):
        """历史消息数量变化事件"""
        # 保存配置
        if self.on_save:
            try:
                cfg = self.get_config()
                self.on_save(cfg)
            except Exception:
                pass
        
        # 通知历史消息变化，用于显示token反馈
        if self.on_history_changed:
            try:
                history_value = self.history_var.get()
                if history_value == "全部":
                    new_count = 0
                else:
                    try:
                        new_count = int(history_value)
                    except ValueError:
                        new_count = 10  # 默认值
                self.on_history_changed(new_count)
            except Exception:
                pass

    def _on_timeout_changed(self, event=None):
        """超时设置变化事件"""
        if self.on_save:
            try:
                cfg = self.get_config()
                self.on_save(cfg)
            except Exception:
                pass

    def _on_manage_prompt(self):
        """管理Prompt按钮事件"""
        if self.on_manage_prompt:
            try:
                self.on_manage_prompt()
            except Exception:
                pass

    def _on_comm_settings(self):
        """通信设置按钮事件"""
        try:
            from .comm_settings import CommSettingsWindow
            window = CommSettingsWindow(self.parent, self.theme, self.current_config)
            window.on_save = self._on_comm_save
        except Exception as e:
            print(f"打开通信设置窗口失败: {e}")

    def _on_comm_save(self, config: dict):
        """通信配置保存回调"""
        if self.on_save:
            try:
                full_config = self.get_config()
                full_config.update(config)
                self.on_save(full_config)
            except Exception:
                pass

    def _on_comm_settings(self):
        """通信设置按钮事件"""
        try:
            window = CommSettingsWindow(self.parent, self.theme, self.current_config)
            window.on_save = self._on_comm_save
        except Exception as e:
            print(f"打开通信设置窗口失败: {e}")

    def _on_comm_save(self, comm_config: dict):
        """保存通信配置"""
        try:
            # 更新当前配置
            self.current_config['comm'] = comm_config
            # 保存到全局配置
            if self.on_save:
                self.on_save(self.current_config)
        except Exception as e:
            print(f"保存通信配置失败: {e}")

    def load_config(self, config: dict):
        """加载配置到控件"""
        try:
            # 设置历史消息
            max_history = config.get('max_history_messages', 5)
            if max_history == 0:
                self.history_var.set("全部")
            else:
                self.history_var.set(str(max_history))
            
            # 设置超时
            timeout = config.get('timeout', 90)
            self.timeout_var.set(str(timeout))
            
        except Exception:
            pass
