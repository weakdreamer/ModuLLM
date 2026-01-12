import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Optional, Dict, Any
import config


class ModelSelectionWindow:
    """模型选择和管理窗口"""

    def __init__(self, parent: tk.Widget, theme: dict):
        self.parent = parent
        self.theme = theme

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("模型管理")
        self.window.geometry("750x550")  # 增加宽度以容纳更多按钮
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # 应用主题
        self._apply_theme()

        # 构建界面
        self._build()

        # 加载模型列表
        self._load_models()

        # 回调
        self.on_model_changed: Optional[Callable[[str], None]] = None

    def _apply_theme(self):
        """应用主题样式"""
        try:
            self.window.configure(bg=self.theme.get('bg', '#ffffff'))
            # 配置ttk样式
            style = ttk.Style()
            style.configure('TLabel', background=self.theme.get('bg', '#ffffff'),
                          foreground=self.theme.get('text', '#000000'))
            style.configure('TCombobox', fieldbackground=self.theme.get('bg', '#ffffff'),
                          background=self.theme.get('bg', '#ffffff'))
            style.configure('TEntry', fieldbackground=self.theme.get('bg', '#ffffff'))
        except Exception:
            pass

    def _build(self):
        """构建界面"""
        main_frame = tk.Frame(self.window, bg=self.theme.get('bg', '#ffffff'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 标题
        title_label = tk.Label(main_frame, text="模型管理",
                             font=('Arial', 14, 'bold'),
                             bg=self.theme.get('bg', '#ffffff'),
                             fg=self.theme.get('text', '#000000'))
        title_label.pack(pady=(0, 20))

        # 模型列表区域
        list_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        list_frame.pack(fill='x', pady=(0, 10))

        tk.Label(list_frame, text="模型列表:", bg=self.theme.get('bg', '#ffffff'),
                fg=self.theme.get('text', '#000000')).grid(row=0, column=0, sticky='w', pady=5)

        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(list_frame, textvariable=self.model_var,
                                       state="readonly", width=30)
        self.model_combo.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        self.model_combo.bind('<<ComboboxSelected>>', self._on_model_selected)

        # 按钮区域
        button_frame = tk.Frame(list_frame, bg=self.theme.get('bg', '#ffffff'))
        button_frame.grid(row=0, column=2, padx=(10, 0))

        self.new_btn = ttk.Button(button_frame, text="新建", command=self._on_new_model)
        self.new_btn.pack(side='left', padx=(0, 5))

        self.edit_btn = ttk.Button(button_frame, text="编辑", command=self._on_edit_model)
        self.edit_btn.pack(side='left', padx=(0, 5))

        self.delete_btn = ttk.Button(button_frame, text="删除", command=self._on_delete_model)
        self.delete_btn.pack(side='left', padx=(0, 5))

        self.test_btn = ttk.Button(button_frame, text="测试连接", command=self._on_test_connection)
        self.test_btn.pack(side='left')

        # 当前模型信息显示区域
        info_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'), relief='groove', bd=2)
        info_frame.pack(fill='x', pady=(10, 20))

        tk.Label(info_frame, text="当前模型信息:", font=('Arial', 10, 'bold'),
                bg=self.theme.get('bg', '#ffffff'), fg=self.theme.get('text', '#000000')).pack(anchor='w', padx=10, pady=5)

        self.info_text = tk.Text(info_frame, height=6, width=60, state='disabled',
                                bg=self.theme.get('bg', '#ffffff'), fg=self.theme.get('text', '#000000'))
        self.info_text.pack(padx=10, pady=(0, 10))

        # 底部按钮
        bottom_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        bottom_frame.pack(fill='x', pady=(10, 0))

        # 关闭按钮
        close_btn = ttk.Button(bottom_frame, text="关闭", command=self.window.destroy)
        close_btn.pack(side='right')

        # 状态标签
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(main_frame, textvariable=self.status_var,
                                   bg=self.theme.get('bg', '#ffffff'),
                                   fg=self.theme.get('text', '#000000'))
        self.status_label.pack(pady=(10, 0))

    def _load_models(self):
        """加载模型列表"""
        try:
            models = config.get_all_models()
            model_names = list(models.keys())
            current_model = config.get_current_model()

            self.model_combo['values'] = model_names
            if current_model and current_model in model_names:
                self.model_var.set(current_model)
                self._display_model_info(current_model)
            elif model_names:
                self.model_var.set(model_names[0])
                self._display_model_info(model_names[0])
            else:
                self._display_model_info(None)
        except Exception as e:
            print(f"加载模型列表失败: {e}")

    def _display_model_info(self, model_name: str | None):
        """显示模型信息"""
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)

        if model_name:
            model_config = config.get_model(model_name)
            if model_config:
                info = f"名称: {model_name}\n"
                info += f"Base URL: {model_config.get('base_url', '')}\n"
                info += f"API Key: {'*' * len(model_config.get('api_key', ''))}\n"
                info += f"模型名称: {model_config.get('model', '')}"
                self.info_text.insert(1.0, info)
            else:
                self.info_text.insert(1.0, "模型配置不存在")
        else:
            self.info_text.insert(1.0, "暂无模型配置，请点击'新建'添加")

        self.info_text.config(state='disabled')

    def _on_model_selected(self, event=None):
        """模型选择变化"""
        model_name = self.model_var.get()
        if model_name:
            self._display_model_info(model_name)
            # 通知外部当前模型已改变
            if self.on_model_changed:
                self.on_model_changed(model_name)

    def _on_new_model(self):
        """新建模型"""
        # 创建输入对话框
        dialog = NewModelDialog(self.window, self.theme)
        self.window.wait_window(dialog.window)

        if dialog.result:
            name, base_url, api_key, model = dialog.result
            # 保存到配置
            model_config = {
                'base_url': base_url,
                'api_key': api_key,
                'model': model
            }
            config.save_model(name, model_config)

            # 刷新列表
            self._load_models()

            # 设置为当前模型
            config.set_current_model(name)
            self.model_var.set(name)
            self._display_model_info(name)

            self.status_var.set("✓ 模型已保存")

    def _on_edit_model(self):
        """编辑模型"""
        current_model = self.model_var.get()
        if not current_model:
            messagebox.showwarning("警告", "请先选择要编辑的模型")
            return

        model_config = config.get_model(current_model)
        if not model_config:
            messagebox.showerror("错误", "模型配置不存在")
            return

        # 创建编辑对话框
        dialog = EditModelDialog(self.window, self.theme, current_model, model_config)
        self.window.wait_window(dialog.window)

        if dialog.result:
            name, base_url, api_key, model = dialog.result
            # 如果名称改变，需要删除旧的
            if name != current_model:
                config.delete_model(current_model)

            # 保存新配置
            model_config = {
                'base_url': base_url,
                'api_key': api_key,
                'model': model
            }
            config.save_model(name, model_config)

            # 刷新列表
            self._load_models()

            # 设置为当前模型
            config.set_current_model(name)
            self.model_var.set(name)
            self._display_model_info(name)

            self.status_var.set("✓ 模型已更新")

    def _on_delete_model(self):
        """删除选定模型"""
        current_model = self.model_var.get()
        if not current_model:
            messagebox.showwarning("警告", "请先选择要删除的模型")
            return

        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除模型 '{current_model}' 吗？\n此操作不可撤销。"):
            return

        try:
            config.delete_model(current_model)
            self.status_var.set("✓ 模型已删除")

            # 如果删除的是当前模型，清空当前模型
            if config.get_current_model() == current_model:
                config.set_current_model("")

            # 刷新列表
            self._load_models()

        except Exception as e:
            messagebox.showerror("错误", f"删除模型失败: {e}")

    def _on_test_connection(self):
        """测试连接"""
        current_model = self.model_var.get()
        if not current_model:
            messagebox.showwarning("警告", "请先选择要测试的模型")
            return

        model_config = config.get_model(current_model)
        if not model_config:
            messagebox.showerror("错误", "模型配置不存在")
            return

        self.status_var.set("正在测试连接...")
        self.test_btn.config(state='disabled')

        # 在后台测试连接
        def test_connection():
            try:
                from api.api_client import ApiClient
                # 创建临时配置
                temp_cfg = {
                    'provider': 'custom',
                    'base_url': model_config['base_url'],
                    'api_key': model_config['api_key'],
                    'model': model_config['model']
                }
                client = ApiClient(temp_cfg)
                reply = client.call_model("Hello, test connection!")
                self.window.after(0, lambda: self._handle_test_result(True, f"连接成功: {reply[:50]}..."))
            except Exception as e:
                self.window.after(0, lambda: self._handle_test_result(False, str(e)))

        import threading
        thread = threading.Thread(target=test_connection, daemon=True)
        thread.start()

    def _handle_test_result(self, success: bool, message: str):
        """处理测试结果"""
        self.test_btn.config(state='normal')
        if success:
            self.status_var.set("✓ 连接成功")
            self.status_label.config(fg='green')
        else:
            self.status_var.set(f"✗ 连接失败: {message}")
            self.status_label.config(fg='red')


class NewModelDialog:
    """新建模型对话框"""

    def __init__(self, parent: tk.Widget, theme: dict):
        self.parent = parent
        self.theme = theme
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("新建模型")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self._build()

    def _build(self):
        main_frame = tk.Frame(self.window, bg=self.theme.get('bg', '#ffffff'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 输入字段
        fields = [
            ("名称:", "name"),
            ("Base URL:", "base_url"),
            ("API Key:", "api_key"),
            ("模型名称:", "model")
        ]

        self.entries = {}
        for i, (label_text, field_name) in enumerate(fields):
            tk.Label(main_frame, text=label_text, bg=self.theme.get('bg', '#ffffff'),
                    fg=self.theme.get('text', '#000000')).grid(row=i, column=0, sticky='w', pady=5)

            if field_name == "api_key":
                entry = ttk.Entry(main_frame, width=30, show="*")
            else:
                entry = ttk.Entry(main_frame, width=30)

            entry.grid(row=i, column=1, sticky='w', padx=(10, 0), pady=5)
            self.entries[field_name] = entry

        # 按钮
        button_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="取消", command=self.window.destroy).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="保存", command=self._on_save).pack(side='right')

    def _on_save(self):
        name = self.entries['name'].get().strip()
        base_url = self.entries['base_url'].get().strip()
        api_key = self.entries['api_key'].get().strip()
        model = self.entries['model'].get().strip()

        if not name:
            messagebox.showwarning("警告", "请输入模型名称")
            return

        # 允许保存不完整的配置，但给出提示
        missing_fields = []
        if not base_url:
            missing_fields.append("Base URL")
        if not api_key:
            missing_fields.append("API Key")
        if not model:
            missing_fields.append("模型名称")

        if missing_fields:
            warning_msg = f"以下字段为空：{', '.join(missing_fields)}\n\n确定要保存不完整的配置吗？"
            if not messagebox.askyesno("确认保存", warning_msg):
                return

        # 检查名称是否已存在
        if config.get_model(name):
            messagebox.showwarning("警告", "模型名称已存在")
            return

        self.result = (name, base_url, api_key, model)
        self.window.destroy()


class EditModelDialog:
    """编辑模型对话框"""

    def __init__(self, parent: tk.Widget, theme: dict, model_name: str, model_config: Dict[str, Any]):
        self.parent = parent
        self.theme = theme
        self.model_name = model_name
        self.model_config = model_config
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("编辑模型")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self._build()
        self._load_data()

    def _build(self):
        main_frame = tk.Frame(self.window, bg=self.theme.get('bg', '#ffffff'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 输入字段
        fields = [
            ("名称:", "name"),
            ("Base URL:", "base_url"),
            ("API Key:", "api_key"),
            ("模型名称:", "model")
        ]

        self.entries = {}
        for i, (label_text, field_name) in enumerate(fields):
            tk.Label(main_frame, text=label_text, bg=self.theme.get('bg', '#ffffff'),
                    fg=self.theme.get('text', '#000000')).grid(row=i, column=0, sticky='w', pady=5)

            if field_name == "api_key":
                entry = ttk.Entry(main_frame, width=30, show="*")
            else:
                entry = ttk.Entry(main_frame, width=30)

            entry.grid(row=i, column=1, sticky='w', padx=(10, 0), pady=5)
            self.entries[field_name] = entry

        # 按钮
        button_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="取消", command=self.window.destroy).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="保存", command=self._on_save).pack(side='right')

    def _load_data(self):
        """加载现有数据"""
        self.entries['name'].insert(0, self.model_name)
        self.entries['base_url'].insert(0, self.model_config.get('base_url', ''))
        self.entries['api_key'].insert(0, self.model_config.get('api_key', ''))
        self.entries['model'].insert(0, self.model_config.get('model', ''))

    def _on_save(self):
        name = self.entries['name'].get().strip()
        base_url = self.entries['base_url'].get().strip()
        api_key = self.entries['api_key'].get().strip()
        model = self.entries['model'].get().strip()

        if not name:
            messagebox.showwarning("警告", "请输入模型名称")
            return

        # 允许保存不完整的配置，但给出提示
        missing_fields = []
        if not base_url:
            missing_fields.append("Base URL")
        if not api_key:
            missing_fields.append("API Key")
        if not model:
            missing_fields.append("模型名称")

        if missing_fields:
            warning_msg = f"以下字段为空：{', '.join(missing_fields)}\n\n确定要保存不完整的配置吗？"
            if not messagebox.askyesno("确认保存", warning_msg):
                return

        # 如果名称改变，检查新名称是否已存在
        if name != self.model_name and config.get_model(name):
            messagebox.showwarning("警告", "模型名称已存在")
            return

        self.result = (name, base_url, api_key, model)
        self.window.destroy()