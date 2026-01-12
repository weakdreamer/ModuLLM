#!/usr/bin/env python3
"""性能测试脚本：测试UI响应性和多线程优化效果"""

import time
import threading
from controller.controller import Controller
from ui.app_ui import AppUI
from api.api_client import ApiClient
from storage import Storage
import config

def test_ui_responsiveness():
    """测试UI响应性"""
    print("开始UI响应性测试...")

    # 初始化组件
    cfg = config.get_config()
    storage = Storage()
    api_client = ApiClient(cfg)
    controller = Controller(None, storage, api_client, cfg)

    # 创建UI（但不启动主循环）
    ui = AppUI(controller)
    controller.ui = ui

    # 测试1: 快速连续输入（模拟用户快速打字）
    print("测试1: 快速连续输入响应...")
    start_time = time.time()
    for i in range(10):
        ui.input_text.insert("1.0", f"测试消息{i}")
        ui.input_text.delete("1.0", "end")
        # 强制更新UI
        ui.root.update()
    end_time = time.time()
    print(".2f")

    # 测试2: 模拟API调用延迟
    print("测试2: 模拟API调用延迟...")
    ui.input_text.insert("1.0", "测试API延迟")

    # 记录开始时间
    call_start = time.time()

    # 模拟发送消息（这会触发异步API调用）
    controller.on_send("测试API延迟")

    # 等待一小段时间，让异步调用开始
    time.sleep(0.1)

    # 检查UI是否仍然响应（应该能立即响应）
    ui_response_start = time.time()
    ui.input_text.delete("1.0", "end")
    ui.input_text.insert("1.0", "UI仍然响应")
    ui.root.update()
    ui_response_end = time.time()

    print(".2f")

    # 等待异步调用完成
    time.sleep(2)  # 等待mock回复

    call_end = time.time()
    print(".2f")

    print("✅ UI响应性测试完成")

if __name__ == "__main__":
    test_ui_responsiveness()