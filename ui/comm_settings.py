import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any
import secrets
import string


class CommSettingsWindow:
    """通信设置窗口"""

    def __init__(self, parent: tk.Widget, theme: dict, current_config: dict = None):
        self.parent = parent
        self.theme = theme
        self.current_config = current_config or {}

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("通信设置")
        self.window.geometry("500x300")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # 应用主题
        self._apply_theme()

        # 构建界面
        self._build()

        # 加载配置
        self._load_config()

        # 回调
        self.on_save: Optional[Callable[[dict], None]] = None

    def _apply_theme(self):
        """应用主题样式"""
        try:
            self.window.configure(bg=self.theme.get('bg', '#ffffff'))
            # 配置ttk样式
            style = ttk.Style()
            style.configure('TLabel', background=self.theme.get('bg', '#ffffff'),
                          foreground=self.theme.get('text', '#000000'))
            style.configure('TCheckbutton', background=self.theme.get('bg', '#ffffff'),
                          foreground=self.theme.get('text', '#000000'))
            style.configure('TEntry', fieldbackground=self.theme.get('bg', '#ffffff'))
            style.configure('TButton', background=self.theme.get('bg', '#ffffff'))
        except Exception:
            pass

    def _build(self):
        """构建界面"""
        main_frame = tk.Frame(self.window, bg=self.theme.get('bg', '#ffffff'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 启用通信
        self.comm_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="启用通信", variable=self.comm_enabled_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,10))

        # 服务器URL
        ttk.Label(main_frame, text="服务器URL:").grid(row=1, column=0, sticky="w", pady=(0,5))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=40)
        self.url_entry.grid(row=1, column=1, sticky="ew", pady=(0,5))

        # 认证密钥
        ttk.Label(main_frame, text="认证密钥:").grid(row=2, column=0, sticky="w", pady=(0,5))
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(main_frame, textvariable=self.key_var, width=40)
        self.key_entry.grid(row=2, column=1, sticky="ew", pady=(0,5))

        # 生成密钥按钮
        self.gen_key_btn = ttk.Button(main_frame, text="生成密钥", command=self._generate_key)
        self.gen_key_btn.grid(row=2, column=2, padx=(5,0), pady=(0,5))

        # 远程模型模式
        self.remote_mode_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="远程模型模式", variable=self.remote_mode_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10,20))

        # 按钮框架
        btn_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        btn_frame.grid(row=4, column=0, columnspan=3, pady=(10,0))

        # 保存和取消按钮
        self.save_btn = ttk.Button(btn_frame, text="保存", command=self._on_save)
        self.save_btn.pack(side='right', padx=(5,0))

        self.cancel_btn = ttk.Button(btn_frame, text="取消", command=self._on_cancel)
        self.cancel_btn.pack(side='right')

    def _generate_key(self):
        """生成随机密钥"""
        alphabet = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(alphabet) for _ in range(32))
        self.key_var.set(key)

    def _load_config(self):
        """加载配置到控件"""
        try:
            self.comm_enabled_var.set(self.current_config.get('comm_enabled', False))
            self.url_var.set(self.current_config.get('comm_url', 'ws://localhost:8765'))
            self.key_var.set(self.current_config.get('comm_key', ''))
            self.remote_mode_var.set(self.current_config.get('remote_mode', False))
        except Exception as e:
            print(f"加载通信配置失败: {e}")

    def _on_save(self):
        """保存配置"""
        try:
            comm_config = {
                'comm_enabled': self.comm_enabled_var.get(),
                'comm_url': self.url_var.get(),
                'comm_key': self.key_var.get(),
                'remote_mode': self.remote_mode_var.get()
            }
            if self.on_save:
                self.on_save(comm_config)
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存通信配置失败: {e}")

    def _on_cancel(self):
        """取消"""
        self.window.destroy()