import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Optional, Dict, Any


class NewPromptDialog:
    """新建Prompt的对话框，包含名称和内容输入"""
    def __init__(self, parent, theme):
        self.parent = parent
        self.theme = theme
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("新建Prompt")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self._apply_theme()
        self._build()
        self.window.wait_window()

    def _apply_theme(self):
        self.window.configure(bg=self.theme.get('bg', '#ffffff'))

    def _build(self):
        main_frame = tk.Frame(self.window, bg=self.theme.get('bg', '#ffffff'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 名称输入
        tk.Label(main_frame, text="Prompt名称:", bg=self.theme.get('bg', '#ffffff'),
                fg=self.theme.get('text', '#000000')).pack(anchor='w', pady=(0, 5))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=50)
        name_entry.pack(fill='x', pady=(0, 15))
        name_entry.focus()

        # 内容输入
        tk.Label(main_frame, text="系统提示内容:", bg=self.theme.get('bg', '#ffffff'),
                fg=self.theme.get('text', '#000000')).pack(anchor='w', pady=(0, 5))
        content_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        content_frame.pack(fill='both', expand=True, pady=(0, 15))

        self.content_text = tk.Text(content_frame, height=10, width=50, wrap='word',
                                   bg=self.theme.get('bg', '#ffffff'), fg=self.theme.get('text', '#000000'))
        scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=scrollbar.set)

        self.content_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 按钮
        button_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        button_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(button_frame, text="确定", command=self._on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(side='right')

    def _on_ok(self):
        name = self.name_var.get().strip()
        content = self.content_text.get('1.0', 'end').strip()
        if not name:
            messagebox.showerror("错误", "请输入Prompt名称")
            return
        if not content:
            messagebox.showerror("错误", "请输入系统提示内容")
            return
        self.result = (name, content)
        self.window.destroy()

    def _on_cancel(self):
        self.window.destroy()


class EditPromptDialog:
    """编辑Prompt的对话框"""
    def __init__(self, parent, theme, current_name, current_content):
        self.parent = parent
        self.theme = theme
        self.current_name = current_name
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("编辑Prompt")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self._apply_theme()
        self._build(current_content)
        self.window.wait_window()

    def _apply_theme(self):
        self.window.configure(bg=self.theme.get('bg', '#ffffff'))

    def _build(self, content):
        main_frame = tk.Frame(self.window, bg=self.theme.get('bg', '#ffffff'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 名称显示（不可编辑）
        tk.Label(main_frame, text=f"Prompt名称: {self.current_name}", bg=self.theme.get('bg', '#ffffff'),
                fg=self.theme.get('text', '#000000')).pack(anchor='w', pady=(0, 15))

        # 内容输入
        tk.Label(main_frame, text="系统提示内容:", bg=self.theme.get('bg', '#ffffff'),
                fg=self.theme.get('text', '#000000')).pack(anchor='w', pady=(0, 5))
        content_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        content_frame.pack(fill='both', expand=True, pady=(0, 15))

        self.content_text = tk.Text(content_frame, height=10, width=50, wrap='word',
                                   bg=self.theme.get('bg', '#ffffff'), fg=self.theme.get('text', '#000000'))
        self.content_text.insert('1.0', content)
        scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=scrollbar.set)

        self.content_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 按钮
        button_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        button_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(button_frame, text="确定", command=self._on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(side='right')

    def _on_ok(self):
        content = self.content_text.get('1.0', 'end').strip()
        if not content:
            messagebox.showerror("错误", "请输入系统提示内容")
            return
        self.result = content
        self.window.destroy()

    def _on_cancel(self):
        self.window.destroy()


class PromptManagementWindow:
    """Prompt管理窗口：新建、编辑、删除和应用Prompt"""

    def __init__(self, parent: tk.Widget, theme: dict, storage: Any, current_prompt: str):
        self.parent = parent
        self.theme = theme
        self.storage = storage
        self.current_prompt = current_prompt

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("Prompt管理")
        self.window.geometry("800x600")  # 增大窗口
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # 应用主题
        self._apply_theme()

        # 构建界面
        self._build()

        # 加载Prompt列表
        self._load_prompts()

        # 回调
        self.on_apply: Optional[Callable[[str], None]] = None

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
        title_label = tk.Label(main_frame, text="Prompt管理",
                             font=('Arial', 14, 'bold'),
                             bg=self.theme.get('bg', '#ffffff'),
                             fg=self.theme.get('text', '#000000'))
        title_label.pack(pady=(0, 20))

        # Prompt列表区域
        list_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'))
        list_frame.pack(fill='x', pady=(0, 10))

        tk.Label(list_frame, text="Prompt列表:", bg=self.theme.get('bg', '#ffffff'),
                fg=self.theme.get('text', '#000000')).grid(row=0, column=0, sticky='w', pady=5)

        self.prompt_var = tk.StringVar()
        self.prompt_combo = ttk.Combobox(list_frame, textvariable=self.prompt_var,
                                       state="readonly", width=30)
        self.prompt_combo.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        self.prompt_combo.bind('<<ComboboxSelected>>', self._on_prompt_selected)

        # 按钮区域
        button_frame = tk.Frame(list_frame, bg=self.theme.get('bg', '#ffffff'))
        button_frame.grid(row=0, column=2, padx=(10, 0))

        self.new_btn = ttk.Button(button_frame, text="新建", command=self._on_new_prompt)
        self.new_btn.pack(side='left', padx=(0, 5))

        self.edit_btn = ttk.Button(button_frame, text="编辑", command=self._on_edit_prompt)
        self.edit_btn.pack(side='left', padx=(0, 5))

        self.delete_btn = ttk.Button(button_frame, text="删除", command=self._on_delete_prompt)
        self.delete_btn.pack(side='left', padx=(0, 5))

        self.apply_btn = ttk.Button(button_frame, text="应用到当前会话", command=self._on_apply_prompt)
        self.apply_btn.pack(side='left')

        # 当前Prompt信息显示区域
        info_frame = tk.Frame(main_frame, bg=self.theme.get('bg', '#ffffff'), relief='groove', bd=2)
        info_frame.pack(fill='x', pady=(10, 20))

        tk.Label(info_frame, text="当前Prompt内容:", font=('Arial', 10, 'bold'),
                bg=self.theme.get('bg', '#ffffff'), fg=self.theme.get('text', '#000000')).pack(anchor='w', padx=10, pady=5)

        text_frame = tk.Frame(info_frame, bg=self.theme.get('bg', '#ffffff'))
        text_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.info_text = tk.Text(text_frame, height=12, width=60, wrap='word', state='disabled',
                                bg=self.theme.get('bg', '#ffffff'), fg=self.theme.get('text', '#000000'))
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)

        self.info_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

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

    def _load_prompts(self):
        """加载Prompt列表"""
        try:
            prompts = self.storage.list_prompts()
            prompt_names = [p['name'] for p in prompts]
            current = self.current_prompt if self.current_prompt in prompt_names else (prompt_names[0] if prompt_names else "")

            self.prompt_combo['values'] = prompt_names
            if current:
                self.prompt_var.set(current)
                self._display_prompt_info(current)
            elif prompt_names:
                self.prompt_var.set(prompt_names[0])
                self._display_prompt_info(prompt_names[0])
            else:
                self._display_prompt_info(None)
        except Exception as e:
            print(f"加载Prompt列表失败: {e}")

    def _display_prompt_info(self, prompt_name: str | None):
        """显示Prompt信息"""
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)

        if prompt_name:
            prompt_record = self.storage.get_prompt(prompt_name)
            if prompt_record:
                content = prompt_record.get('content', '')
                self.info_text.insert(1.0, content)
            else:
                self.info_text.insert(1.0, "Prompt内容不存在")
        else:
            self.info_text.insert(1.0, "暂无Prompt配置，请点击'新建'添加")

        self.info_text.config(state='disabled')

    def _on_prompt_selected(self, event=None):
        """选择Prompt事件"""
        prompt_name = self.prompt_var.get()
        if prompt_name:
            self._display_prompt_info(prompt_name)

    def _on_new_prompt(self):
        """新建Prompt"""
        dialog = NewPromptDialog(self.window, self.theme)
        if dialog.result:
            name, content = dialog.result
            if self.storage.get_prompt(name):
                messagebox.showerror("错误", f"Prompt '{name}' 已存在")
                return
            try:
                self.storage.upsert_prompt(name, "system", content)
                self.status_var.set("✓ Prompt已创建")
                self._load_prompts()
            except Exception as e:
                messagebox.showerror("错误", f"创建Prompt失败: {e}")

    def _on_edit_prompt(self):
        """编辑Prompt"""
        current_name = self.prompt_var.get()
        if not current_name:
            messagebox.showwarning("警告", "请先选择要编辑的Prompt")
            return

        prompt_record = self.storage.get_prompt(current_name)
        if not prompt_record:
            messagebox.showerror("错误", "Prompt不存在")
            return

        dialog = EditPromptDialog(self.window, self.theme, current_name, prompt_record['content'])
        if dialog.result:
            try:
                self.storage.upsert_prompt(current_name, "system", dialog.result)
                self.status_var.set("✓ Prompt已更新")
                self._display_prompt_info(current_name)
            except Exception as e:
                messagebox.showerror("错误", f"更新Prompt失败: {e}")

    def _on_delete_prompt(self):
        """删除Prompt"""
        current_name = self.prompt_var.get()
        if not current_name:
            messagebox.showwarning("警告", "请先选择要删除的Prompt")
            return

        if current_name == "default":
            messagebox.showerror("错误", "不能删除默认Prompt")
            return

        if not messagebox.askyesno("确认删除", f"确定要删除Prompt '{current_name}' 吗？\n此操作不可撤销。"):
            return

        try:
            if self.storage.delete_prompt(current_name):
                self.status_var.set("✓ Prompt已删除")
                self._load_prompts()
            else:
                messagebox.showerror("错误", "删除Prompt失败")
        except Exception as e:
            messagebox.showerror("错误", f"删除Prompt失败: {e}")

    def _on_apply_prompt(self):
        """应用到当前会话"""
        prompt_name = self.prompt_var.get()
        if not prompt_name:
            messagebox.showwarning("警告", "请先选择Prompt")
            return

        if self.on_apply:
            try:
                self.on_apply(prompt_name)
                self.status_var.set(f"✓ 已应用Prompt '{prompt_name}' 到当前会话")
            except Exception as e:
                messagebox.showerror("错误", f"应用Prompt失败: {e}")
        else:
            messagebox.showwarning("警告", "应用回调未设置")