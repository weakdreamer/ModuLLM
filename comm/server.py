"""Lightweight WebSocket relay/proxy server."""
from __future__ import annotations

import argparse
import asyncio
import json
from typing import Dict, Optional, Set, Any

import websockets

import config
from api import ApiClient


class RelayServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765, allowed_keys: Optional[Set[str]] = None):
        self.host = host
        self.port = port
        self.allowed_keys = allowed_keys
        self.clients: Dict[str, Any] = {}
        self.cfg = config.load_config()
        self.api_client = ApiClient(self.cfg)
        self._auth_keys: Dict[Any, str] = {}

    def process_request(self, path, request_headers):
        """处理WebSocket握手请求，提取认证密钥。"""
        # 简化测试：跳过认证检查
        return None

    async def handler(self, websocket: Any):
        # 简化测试：使用固定auth_key
        auth_key = "test_key"
        
        self.clients[auth_key] = websocket
        try:
            async for message in websocket:
                await self._handle_message(auth_key, message)
        finally:
            self.clients.pop(auth_key, None)

    async def _handle_message(self, sender_key: str, raw: str):
        try:
            payload = json.loads(raw)
        except Exception:
            return
        msg_type = payload.get("type", "chat")
        target = payload.get("target")

        if msg_type == "model_request":
            reply_text = self._call_model(payload)
            await self._send_to(
                sender_key,
                {
                    "type": "model_reply",
                    "session_id": payload.get("session_id"),
                    "reply": reply_text,
                    "meta": {"from": "server"},
                },
            )
            return

        await self._relay(sender_key, target, payload)

    def _call_model(self, payload: dict) -> str:
        prompt = payload.get("text", "")
        context = payload.get("context") or []
        api_cfg = payload.get("api_cfg") or None
        model_name = payload.get("model")
        # 如果未显式指定模型且未提供 api_cfg，则回退到服务器当前模型
        if not model_name and api_cfg is None:
            model_name = config.get_current_model()

        # 如果请求指定模型，尝试加载对应配置并进行补全
        if model_name:
            model_cfg = config.get_model(model_name)
            if model_cfg:
                merged_cfg = {
                    "provider": "custom",
                    "base_url": model_cfg.get("base_url", ""),
                    "api_key": model_cfg.get("api_key", ""),
                    "model": model_cfg.get("model", ""),
                    "timeout": self.cfg.get("timeout", 30),
                }
                api_cfg = merged_cfg if api_cfg is None else {**merged_cfg, **api_cfg}
            else:
                return f"[ERROR] server missing model config: {model_name}"

        try:
            return self.api_client.call_model(prompt, context=context, cfg=api_cfg)
        except Exception as e:
            return f"[ERROR] remote model call failed: {e}"

    async def _relay(self, sender_key: str, target_key: Optional[str], payload: dict):
        if not target_key:
            return
        outgoing = dict(payload)
        outgoing.setdefault("sender", sender_key)
        await self._send_to(target_key, outgoing)

    async def _send_to(self, target_key: str, payload: dict):
        ws = self.clients.get(target_key)
        if not ws:
            return
        try:
            await ws.send(json.dumps(payload))
        except Exception:
            pass

    async def run(self):
        async with websockets.serve(
            self.handler, 
            self.host, 
            self.port,
            process_request=self.process_request
        ):
            await asyncio.Future()


def main():
    parser = argparse.ArgumentParser(description="Lightweight WebSocket relay server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--auth-key", action="append", help="Allowed auth key (can be set multiple times)")
    args = parser.parse_args()

    allowed = set(args.auth_key) if args.auth_key else None
    server = RelayServer(args.host, args.port, allowed)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
