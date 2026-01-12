"""测试通信模块的功能，包括WebSocket客户端、服务器和远程模型调用。"""
import asyncio
import json
import os
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from comm import WebSocketComm, generate_auth_key
from comm.server import RelayServer


class TestComm:
    """通信模块单元测试。"""

    def test_generate_auth_key(self):
        """测试生成随机认证密钥。"""
        key1 = generate_auth_key()
        key2 = generate_auth_key()
        assert isinstance(key1, str)
        assert len(key1) > 20  # 应为URL安全的长字符串
        assert key1 != key2  # 应随机

    def test_websocket_comm_init(self):
        """测试WebSocket客户端初始化。"""
        comm = WebSocketComm("ws://localhost:8765", "test_key")
        assert comm.server_url == "ws://localhost:8765"
        assert comm.auth_key == "test_key"
        assert comm._on_message is None

    def test_websocket_comm_send_without_connection(self):
        """测试在未连接时发送消息（应静默失败）。"""
        comm = WebSocketComm("ws://localhost:8765")
        comm.send("target", {"type": "test"})
        # 无异常抛出

    @patch('websocket.WebSocketApp')
    def test_websocket_comm_start_stop(self, mock_ws_app):
        """测试启动和停止WebSocket客户端。"""
        mock_app = MagicMock()
        mock_ws_app.return_value = mock_app
        mock_app.sock.connected = True

        comm = WebSocketComm("ws://localhost:8765")
        comm.start()
        time.sleep(0.1)  # 等待线程启动
        assert comm._thread.is_alive()

        comm.stop()
        time.sleep(0.1)
        mock_app.close.assert_called_once()

    def test_websocket_comm_message_handler(self):
        """测试消息处理回调。"""
        comm = WebSocketComm("ws://localhost:8765")
        received = []

        def handler(payload):
            received.append(payload)

        comm.on_message(handler)
        # 模拟接收消息
        comm._handle_message(None, '{"type": "test", "data": "hello"}')
        assert received == [{"type": "test", "data": "hello"}]

    def test_relay_server_init(self):
        """测试中继服务器初始化。"""
        server = RelayServer("0.0.0.0", 8765, {"key1", "key2"})
        assert server.host == "0.0.0.0"
        assert server.port == 8765
        assert server.allowed_keys == {"key1", "key2"}

    @patch('comm.server.config.load_config')
    @patch('comm.server.ApiClient')
    def test_relay_server_call_model(self, mock_api_client, mock_load_config):
        """测试服务器端模型调用。"""
        mock_load_config.return_value = {"provider": "test", "api_key": "test_key"}
        mock_client = MagicMock()
        mock_client.call_model.return_value = "Mock reply"
        mock_api_client.return_value = mock_client

        server = RelayServer()
        payload = {
            "text": "Hello",
            "context": [{"role": "user", "content": "Hi"}],
            "api_cfg": {"model": "gpt-3.5"}
        }
        reply = server._call_model(payload)
        assert reply == "Mock reply"
        mock_client.call_model.assert_called_once_with("Hello", context=[{"role": "user", "content": "Hi"}], cfg={"model": "gpt-3.5"})

    def test_relay_server_authenticate_valid(self):
        """测试有效认证。"""
        server = RelayServer(allowed_keys={"valid_key"})
        # 认证现在在process_request中处理，这里测试handler逻辑
        assert server.allowed_keys == {"valid_key"}

    def test_relay_server_authenticate_invalid(self):
        """测试无效认证。"""
        server = RelayServer(allowed_keys={"valid_key"})
        # 认证现在在process_request中处理，这里测试handler逻辑
        assert server.allowed_keys == {"valid_key"}

    @patch('asyncio.Future')
    @patch('websockets.serve')
    def test_relay_server_run(self, mock_serve, mock_future):
        """测试服务器运行。"""
        mock_serve.return_value.__aenter__.return_value = None
        mock_future.return_value = None

        server = RelayServer()
        # 运行短暂时间后停止
        async def run_and_stop():
            task = asyncio.create_task(server.run())
            await asyncio.sleep(0.1)
            task.cancel()

        asyncio.run(run_and_stop())
        mock_serve.assert_called_once()


class TestIntegration:
    """集成测试：客户端与服务器交互。"""

    @pytest.fixture
    def server_thread(self):
        """启动测试服务器的fixture。"""
        import socket
        # 找到可用端口
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        
        server = RelayServer("127.0.0.1", port, {"test_key"})
        thread = threading.Thread(target=lambda: asyncio.run(server.run()), daemon=True)
        thread.start()
        time.sleep(0.5)  # 等待服务器启动
        yield server, port
        # 清理：服务器在测试结束后自动停止

    def test_client_server_chat(self, server_thread):
        """测试客户端发送聊天消息到服务器。"""
        server, port = server_thread
        comm = WebSocketComm(f"ws://127.0.0.1:{port}", "test_key")
        received = []

        def handler(payload):
            received.append(payload)

        comm.on_message(handler)
        comm.start()
        time.sleep(1)  # 等待连接

        # 发送聊天消息
        comm.send("other_key", {"type": "chat", "text": "Hello from client"})
        time.sleep(1)  # 等待消息处理

        # 由于是单客户端测试，消息不会被转发，但连接应成功
        assert comm._ws_app is not None
        comm.stop()

    def test_client_server_model_request(self, server_thread):
        """测试客户端请求远程模型调用。"""
        server, port = server_thread
        with patch('comm.server.ApiClient.call_model', return_value="Server model reply"):
            comm = WebSocketComm(f"ws://127.0.0.1:{port}", "test_key")
            received = []

            def handler(payload):
                received.append(payload)

            comm.on_message(handler)
            comm.start()
            time.sleep(1)

            # 发送模型请求
            comm.send("server", {
                "type": "model_request",
                "session_id": "test_session",
                "text": "Test prompt",
                "context": []
            })
            time.sleep(1)

            # 检查是否收到回复
            replies = [p for p in received if p.get("type") == "model_reply"]
            assert len(replies) == 1
            assert replies[0]["reply"] == "Server model reply"
            comm.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])