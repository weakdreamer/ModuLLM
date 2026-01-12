"""简单的 API 客户端封装：支持真实请求或在未配置时返回 mock 回复。"""
import time
from typing import List, Dict, Any

import requests


class ApiClient:
    # 内置API服务商配置
    PROVIDERS = {
        "custom": {
            "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            "payload_format": "openai",
            "key_param": "api_key",
            "default_model": "gpt-3.5-turbo"
        }
    }

    def __init__(self, cfg: Dict[str, Any]):
        """初始化客户端，cfg 应为 `config.get_config()` 的返回值或类似字典。"""
        self.cfg = cfg

    def call_model(self, prompt: str, context: List[Dict[str, Any]] | None = None, cfg: Dict[str, Any] | None = None) -> str:
        """调用大模型 API。

        如果未配置 `api_key` 或 `provider`，返回本地 mock 回复，便于离线开发与测试。
        返回字符串（模型回复）。
        """
        context = context or []
        # 使用传入的cfg或默认的self.cfg
        api_cfg = cfg or self.cfg
        provider = api_cfg.get("provider", "")
        api_key = api_cfg.get("api_key", "")
        timeout = api_cfg.get("timeout", 30)

        # Mock 模式
        if not provider or not api_key:
            time.sleep(0.3)
            return f"[MOCK REPLY] 接收到: {prompt[:200]}"

        if provider not in self.PROVIDERS:
            return f"[ERROR] 不支持的API服务商: {provider}"

        provider_config = self.PROVIDERS[provider]
        base_url = api_cfg.get("base_url", provider_config.get("base_url", ""))

        # 为不同格式添加正确的端点路径
        if provider_config["payload_format"] == "openai":
            if not base_url.endswith("/chat/completions"):
                base_url = base_url.rstrip("/") + "/chat/completions"
        elif provider_config["payload_format"] == "gemini":
            # Gemini API的端点格式可能不同，这里先保持原样
            pass

        headers = provider_config["headers"](api_key)
        payload = self._build_payload(prompt, context, provider_config["payload_format"], provider, api_cfg)

        try:
            resp = requests.post(base_url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_response(data, provider_config["payload_format"])
        except requests.exceptions.HTTPError as e:
            # 提供更详细的错误信息
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = f" - {error_data.get('error', {}).get('message', str(error_data))}"
            except:
                error_detail = f" - Status: {e.response.status_code}"
            return f"[ERROR] API调用失败: {e}{error_detail}"
        except Exception as e:
            return f"[ERROR] API调用失败: {e}"

    def _build_payload(self, prompt: str, context: List[Dict[str, Any]], format_type: str, provider: str, api_cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """根据不同的API格式构建请求payload。"""
        api_cfg = api_cfg or self.cfg
        provider_config = self.PROVIDERS.get(provider, {})
        default_model = api_cfg.get("model", provider_config.get("default_model", "gpt-3.5-turbo"))

        if format_type == "openai":
            # OpenAI兼容格式
            messages = []
            for msg in context:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": prompt})
            return {
                "model": default_model,
                "messages": messages,
                "temperature": 0.7
            }
        elif format_type == "gemini":
            # Gemini格式
            contents = []
            for msg in context:
                contents.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})

            # Gemini的角色映射：user -> user, assistant -> model
            gemini_contents = []
            for msg in context:
                role = "user" if msg["role"] == "user" else "model"
                gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})

            gemini_contents.append({"role": "user", "parts": [{"text": prompt}]})

            return {
                "contents": gemini_contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
        else:
            return {"prompt": prompt, "context": context}

    def _parse_response(self, data: Dict[str, Any], format_type: str) -> str:
        """根据不同的API格式解析响应。"""
        if format_type == "openai":
            # OpenAI兼容格式
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return str(data)
        elif format_type == "gemini":
            # Gemini格式
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0]["text"]
            return str(data)
        else:
            return data.get("reply") or data.get("text") or str(data)


__all__ = ["ApiClient"]
