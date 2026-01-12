"""协调 UI、存储与 API 的控制器。"""
from typing import Any, Dict, List
import tkinter as tk
from tkinter import messagebox
import threading
import queue


class Controller:
    def __init__(self, ui: Any, storage: Any, api_client: Any, cfg: Dict[str, Any], prompt_manager: Any = None, comm: Any = None):
        self.ui = ui
        self.storage = storage
        self.api_client = api_client
        self.cfg = cfg
        self.prompt_manager = prompt_manager
        self.comm = comm
        self.current_session: str | None = None
        self.current_prompt: str = "default"  # 默认Prompt
        # 线程安全的队列用于后台线程与UI线程通信
        self.result_queue = queue.Queue()
        if self.comm:
            try:
                self.comm.on_message(self._on_comm_message)
                self.comm.start()
            except Exception:
                pass

    def on_delete_message(self, session_id: str, msg_index: int):
        """删除指定会话中的单条消息（按索引）。"""
        try:
            sess = self.storage.get_session(session_id)
            msgs = sess.get("messages", [])
            if 0 <= msg_index < len(msgs):
                del msgs[msg_index]
                # 覆盖并保存
                self.storage.sessions[session_id]["messages"] = msgs
                self.storage.save()
                # 如果当前会话，刷新UI显示
                if self.ui and getattr(self, 'current_session', None) == session_id:
                    self.ui.show_messages(msgs)
        except Exception:
            pass

    def on_delete_messages(self, session_id: str, indices: list):
        """批量删除多条消息，indices 为索引列表。"""
        try:
            if not indices:
                return
            sess = self.storage.get_session(session_id)
            msgs = sess.get("messages", [])
            # 删除时从高到低删除以避免索引偏移
            for idx in sorted(indices, reverse=True):
                if 0 <= idx < len(msgs):
                    del msgs[idx]
            self.storage.sessions[session_id]["messages"] = msgs
            self.storage.save()
            if self.ui and getattr(self, 'current_session', None) == session_id:
                self.ui.show_messages(msgs)
        except Exception:
            pass

    def on_export_messages(self, session_id: str, indices: list, filename: str, format_type: str = 'txt'):
        """导出选中的消息到文件，支持 txt/md/json（简单实现）。"""
        try:
            if not indices:
                return
            sess = self.storage.get_session(session_id)
            msgs = sess.get("messages", [])
            selected = [msgs[i] for i in sorted(indices) if 0 <= i < len(msgs)]
            if not selected:
                return

            if format_type == 'txt':
                with open(filename, 'w', encoding='utf-8') as f:
                    for m in selected:
                        role = m.get('role', 'unknown')
                        content = m.get('content', '')
                        f.write(f"{role.title()}: {content}\n\n")
            elif format_type == 'md':
                with open(filename, 'w', encoding='utf-8') as f:
                    for m in selected:
                        role = m.get('role', 'unknown')
                        content = m.get('content', '')
                        f.write(f"**{role.title()}**: {content}\n\n")
            elif format_type == 'json':
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({'messages': selected}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def on_retry_message(self, session_id: str, msg_index: int):
        """重试某条用户消息（将其作为新请求发送）。只对 user 类型有效。"""
        try:
            sess = self.storage.get_session(session_id)
            msgs = sess.get("messages", [])
            if 0 <= msg_index < len(msgs):
                msg = msgs[msg_index]
                if msg.get('role') == 'user':
                    # 直接调用 on_send 重新发送
                    self.on_send(msg.get('content', ''))
        except Exception:
            pass

    def on_new_session(self, title: str):
        # 保存当前会话草稿
        try:
            if self.current_session and hasattr(self.ui, 'input_text'):
                draft = self.ui.input_text.get('1.0', tk.END).strip()
                if self.current_session in self.storage.sessions:
                    self.storage.sessions[self.current_session]['draft'] = draft
                    self.storage.save()
        except Exception:
            pass

        sid = self.storage.create_session(title)
        self.current_session = sid
        self.ui.refresh_sessions(self.storage.list_sessions())
        self.ui.show_messages([])

    def on_select_session(self, session_id: str):
        # 保存当前会话的草稿（如果存在）
        try:
            if self.current_session and hasattr(self.ui, 'input_text'):
                draft = self.ui.input_text.get('1.0', tk.END).strip()
                if self.current_session in self.storage.sessions:
                    self.storage.sessions[self.current_session]['draft'] = draft
                    self.storage.save()
        except Exception:
            pass

        self.current_session = session_id
        sess = self.storage.get_session(session_id)
        self.ui.show_messages(sess.get("messages", []))
        # 加载草稿到输入区
        try:
            draft_text = sess.get('draft', '')
            if hasattr(self.ui, 'input_text'):
                self.ui.input_text.delete('1.0', tk.END)
                if draft_text:
                    self.ui.input_text.insert('1.0', draft_text)
        except Exception:
            pass

    def on_send(self, prompt: str):
        if not self.current_session:
            self.current_session = self.storage.create_session("Auto")
        self.storage.append_message(self.current_session, "user", prompt)

        # 立即显示用户消息（只追加气泡，避免整页重绘）
        try:
            self.ui.add_message_bubble('user', prompt)
        except Exception:
            # 回退到完整渲染
            self.ui.show_messages(self.storage.get_session(self.current_session).get("messages", []))

        use_remote = bool(self.comm and self.cfg.get("comm_enabled") and self.cfg.get("comm_use_remote_model"))

        # 显示"正在思考..."状态
        self._show_thinking_message()

        if use_remote:
            self._send_remote_model_request(prompt)
            return

        # 在后台线程中执行API调用
        thread = threading.Thread(target=self._call_api_async, args=(prompt,))
        thread.daemon = True
        thread.start()

    def _show_thinking_message(self):
        """显示正在思考的临时气泡"""
        if not self.ui:
            return
        # 在UI主线程添加临时气泡
        self.ui.root.after(0, lambda: self.ui.add_message_bubble('assistant', '正在思考...', temporary=True))

    def _build_context_messages(self):
        """构建发送给AI的上下文消息，包括完整的对话历史"""
        all_messages = self.storage.get_session(self.current_session).get("messages", []) if self.current_session else []
        # 包括完整的对话历史，这样AI才能理解上下文
        # 不排除最后一条消息，因为完整的对话历史对AI很重要
        max_history = self.cfg.get("max_history_messages", 10)
        if max_history > 0:
            # 如果设置了最大历史数量，则取最近的N条消息
            return all_messages[-max_history:] if len(all_messages) > max_history else all_messages
        return all_messages

    def _send_remote_model_request(self, prompt: str):
        if not self.comm:
            return
        try:
            import config
            model_name = config.get_current_model()
            context = self._build_context_messages()
            payload = {
                "type": "model_request",
                "session_id": self.current_session,
                "text": prompt,
                "context": context,
                "prompt_name": self.current_prompt,
                "model": model_name,
            }
            self.comm.send(target="server", payload=payload)
        except Exception:
            pass

    def _call_api_async(self, prompt: str):
        """在后台线程中异步调用API"""
        try:
            # 动态获取当前模型配置
            import config
            current_model = config.get_current_model()
            if not current_model:
                reply = "[ERROR] 未选择模型，请先选择模型"
                self.result_queue.put(reply)
                return

            model_config = config.get_model(current_model)
            if not model_config:
                reply = f"[ERROR] 模型 '{current_model}' 配置不存在"
                self.result_queue.put(reply)
                return

            # 创建API客户端配置
            api_cfg = {
                'provider': 'custom',
                'base_url': model_config['base_url'],
                'api_key': model_config['api_key'],
                'model': model_config['model'],
                'timeout': self.cfg.get('timeout', 30)
            }

            # 根据设置获取指定数量的历史消息作为context
            context = self._build_context_messages()

            # 应用Prompt
            if self.prompt_manager:
                from core.ports import Message
                context_messages = [Message(m['role'], m['content'], m['timestamp']) for m in context]
                context_messages = self.prompt_manager.apply_prompt(context_messages, self.current_prompt)
                context = [{'role': m.role, 'content': m.content, 'timestamp': m.timestamp} for m in context_messages]

            reply = self.api_client.call_model(prompt, context=context, cfg=api_cfg)
        except Exception as e:
            reply = f"[ERROR] 调用 API 失败: {e}"

        # 将结果放入线程安全队列，由UI线程处理
        self.result_queue.put(reply)

    def _update_ui_with_reply(self, reply: str):
        """在主线程中更新UI显示回复"""
        # 使用气泡渲染回复并保存
        try:
            self.ui.add_message_bubble('assistant', reply)
        except Exception:
            # 如果气泡渲染失败，回退到完整渲染
            self.ui.show_messages(self.storage.get_session(self.current_session).get("messages", []) + [{'role':'assistant','content':reply}])

        # 保存回复到存储
        self.storage.append_message(self.current_session, "assistant", reply)

    def on_update_config(self, new_cfg: Dict[str, Any]):
        # 更新内存 cfg 并持久化
        for k, v in new_cfg.items():
            self.cfg[k] = v
        try:
            import config
            config.save_config(self.cfg)
        except Exception:
            pass

    def _infer_provider_from_config(self, model_config: Dict[str, Any]) -> str:
        """从模型配置推断provider"""
        base_url = model_config.get("base_url", "").lower()
        if "deepseek.com" in base_url:
            return "deepseek"
        elif "siliconflow.cn" in base_url:
            return "siliconflow"
        elif "googleapis.com" in base_url:
            return "gemini"
        elif "x.ai" in base_url:
            return "grok"
        else:
            return "custom"  # 默认值

    def on_update_history_messages(self, new_count: int):
        """更新历史消息数量设置并显示token统计"""
        from token_calculator import TokenCalculator
        import config

        # 更新配置
        self.cfg["max_history_messages"] = new_count
        config.save_config(self.cfg)

        # 如果有当前会话，计算并显示token统计
        if self.current_session:
            session = self.storage.get_session(self.current_session)
            all_messages = session.get("messages", [])
            
            # 根据新设置计算要发送的上下文消息（包括完整的对话历史）
            if new_count > 0:
                context_messages = all_messages[-new_count:] if len(all_messages) > new_count else all_messages
            else:
                context_messages = all_messages

            # 计算上下文的token数（包括完整的对话历史）
            context_tokens = TokenCalculator.calculate_messages_tokens(context_messages)
            
            # 获取当前输入草稿（如果有）
            draft_content = session.get("draft", "").strip()
            draft_tokens = TokenCalculator.estimate_tokens(draft_content) if draft_content else 0
            
            # 总token数 = 历史上下文 + 当前输入
            total_tokens = context_tokens + draft_tokens
            
            # 从当前模型推断provider和model
            current_model_name = config.get_current_model()
            if current_model_name:
                model_config = config.get_model(current_model_name)
                if model_config:
                    provider = self._infer_provider_from_config(model_config)
                    model = model_config.get("model", "")
                else:
                    provider = ""
                    model = ""
            else:
                provider = ""
                model = ""

            # 检查token使用情况
            token_info = TokenCalculator.check_token_usage(context_messages + ([{'content': draft_content}] if draft_content else []), provider, model)

            # 构建消息
            title = "历史消息设置已更新"
            message = f"历史消息数量：{new_count if new_count > 0 else '全部'}\n\n"
            message += f"对话历史：{len(context_messages)} 条消息\n"
            message += f"历史Token：{context_tokens}\n"
            if draft_tokens > 0:
                message += f"当前输入Token：{draft_tokens}\n"
                message += f"总预计Token：{total_tokens}\n"
            message += f"模型限制：{token_info['limit']} tokens\n"
            message += f"使用率：{token_info['usage_percent']:.2f}%\n\n"

            if token_info['is_over_limit']:
                message += "⚠️ 警告：Token使用超过限制！\n"
            elif token_info['warning_level'] == 'high':
                message += "⚠️ 高使用率，请注意上下文长度。\n"
            elif token_info['warning_level'] == 'medium':
                message += "ℹ️ 中等使用率，建议监控。\n"

            messagebox.showinfo(title, message)

    def on_update_timeout(self, timeout: int):
        """更新超时设置"""
        self.cfg["timeout"] = timeout
        import config
        config.save_config(self.cfg)

        # 显示确认信息
        messagebox.showinfo("超时设置已更新", f"API请求超时时间已设置为 {timeout} 秒")

    def on_prompt_changed(self, prompt_name: str):
        """更新当前Prompt"""
        self.current_prompt = prompt_name

    def on_manage_prompt(self):
        """打开Prompt管理窗口"""
        if not self.ui:
            return
        from ui.prompt_management import PromptManagementWindow
        window = PromptManagementWindow(self.ui.root, self.ui._theme, self.storage, self.current_prompt)
        window.on_apply = lambda name: self.on_prompt_changed(name)

    def on_rename_session(self, session_id: str, new_name: str):
        """重命名会话"""
        self.storage.rename_session(session_id, new_name)
        self.ui.refresh_sessions(self.storage.list_sessions())

    def on_delete_session(self, session_id: str):
        """删除会话"""
        if self.storage.delete_session(session_id):
            # 如果删除的是当前会话，清空当前会话
            if self.current_session == session_id:
                self.current_session = None
                self.ui.show_messages([])
            self.ui.refresh_sessions(self.storage.list_sessions())

    def on_export_session(self, session_id: str, filename: str, format_type: str):
        """导出会话"""
        session = self.storage.get_session(session_id)
        if not session.get("messages"):
            return

        try:
            if format_type == "txt":
                self._export_as_txt(session, filename)
            elif format_type == "md":
                self._export_as_markdown(session, filename)
            elif format_type == "json":
                self._export_as_json(session, filename)
        except Exception as e:
            import tkinter as tk
            from tkinter import messagebox
            messagebox.showerror("导出失败", f"导出失败: {str(e)}")

    def _export_as_txt(self, session: Dict[str, Any], filename: str):
        """导出为TXT格式"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"会话: {session.get('title', 'Untitled')}\n")
            f.write("=" * 50 + "\n\n")
            for msg in session.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                f.write(f"{role.title()}: {content}\n\n")

    def _export_as_markdown(self, session: Dict[str, Any], filename: str):
        """导出为Markdown格式"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {session.get('title', 'Untitled')}\n\n")
            for msg in session.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if role == "user":
                    f.write(f"**用户**: {content}\n\n")
                elif role == "assistant":
                    f.write(f"**助手**: {content}\n\n")
                else:
                    f.write(f"**{role.title()}**: {content}\n\n")

    def _export_as_json(self, session: Dict[str, Any], filename: str):
        """导出为JSON格式"""
        import json
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

    def _on_comm_message(self, payload: Dict[str, Any]):
        """处理来自通信模块的消息"""
        try:
            msg_type = payload.get("type")
            session_id = payload.get("session_id") or self.current_session
            if not session_id:
                session_id = self.storage.create_session("Remote")
            if session_id not in self.storage.sessions:
                self.storage.sessions[session_id] = {"session_id": session_id, "title": "Remote", "draft": "", "messages": []}

            if msg_type == "model_reply":
                reply = payload.get("reply", "")
                if session_id == self.current_session:
                    self.result_queue.put(reply)
                else:
                    self.storage.append_message(session_id, "assistant", reply)
                return

            if msg_type == "chat":
                text = payload.get("text", "")
                role = payload.get("sender", "assistant")
                if session_id == self.current_session:
                    import datetime
                    ts = payload.get("timestamp") or datetime.datetime.now(datetime.UTC).isoformat()
                    self.result_queue.put({"role": role, "content": text, "timestamp": ts})
                else:
                    self.storage.append_message(session_id, role, text)
                return
        except Exception:
            pass


__all__ = ["Controller"]
