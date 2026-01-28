###   这是一个纯粹AI生成的程序，仅限于最低限度的能跑，能实现核心功能：输入key之后可以和对应的大模型对话，有一个能看的UI。


# LLM 客户端（模块化示例）

这是一个模块化的 Python 桌面应用（教学/原型），用于与多家 LLM 提供商交互。项目以 Tkinter 提供简易 GUI，支持会话管理、消息历史和 token 统计。

## 概览
- 语言：Python 3.10+
- GUI：Tkinter
- 存储：JSON 文件持久化会话与消息（`storage/data.json`）
- 架构：MVC-like，控制器协调 UI、API、存储
- 异步：线程 + 队列，避免阻塞 UI

## 项目结构（主要文件）
```
├── main.py                # 程序入口
├── performance_test.py    # 性能测试脚本
├── token_calculator.py    # Token 估算工具
├── requirements.txt       # 依赖
├── api/
│   └── api_client.py      # 多提供商 API 封装（含 mock）
├── config/
│   ├── __init__.py        # 配置加载/保存
│   └── config.json        # 默认配置
├── controller/
│   └── controller.py      # 调度 UI / API / 存储
├── storage/
│   └── __init__.py        # JSON 持久化（storage/data.json）
├── ui/                    # Tkinter 组件
│   ├── app_ui.py
│   ├── input_area.py
│   ├── session_list.py
│   ├── message_renderer.py
│   ├── config_panel.py
│   └── ...
├── tests/                 # pytest 测试
│   ├── conftest.py
│   └── test_*.py
└── scripts/
    └── clear_sessions.py
```

## 关键功能与约定
- 多模型提供商：Gemini、SiliconFlow、DeepSeek、Grok，缺省使用本地 mock。
- 消息格式：`{"role": "user|assistant", "content": str, "timestamp": ISO}`。
- 历史裁剪：使用配置项 `max_history_messages` 控制上下文长度。
- UI 更新：必须在主线程，后台线程通过队列 + `root.after` 回传结果。

## 快速开始
1) 可选：创建虚拟环境

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2) 安装依赖

```powershell
pip install -r requirements.txt
```

3) 运行应用（需用模块方式）

```powershell
python -m main
```

4) 运行测试

```powershell
pytest
```

## 配置说明
- 配置文件：`config/config.json`，包含 provider、API Key、历史消息条数等。
- 未配置 API Key 时使用 mock 回复，便于开发/演示。
- UI 内可设置历史消息数量与 token 估算。

### 快速配置（推荐）

项目支持“开箱即用”运行：若仓库中不存在 `config/config.json` 或 `storage/data.db`，程序会自动创建默认配置与数据库。

推荐做法：

1. 从示例文件复制并填充你的键值：

```powershell
copy config\config.example.json config\config.json
# 然后编辑 config\config.json，将 <YOUR_API_KEY> 替换为你的密钥（或在 CI/环境变量注入）
```

2. 为安全起见，仓库中不应包含真实密钥。我们已提供 `config/config.example.json`，并将 `config/config.json` 加入 `.gitignore`。

3. 如果你之前不小心将真实密钥提交到 Git 历史，请在撤回或旋转密钥后使用 `git filter-repo` 或 BFG 清理历史。

示例命令：

```bash
# 从当前索引中移除并提交（仅移除索引，不删除本地文件）
git rm --cached config/config.json
git commit -m "Remove sensitive config from repo"
```

如果需要，我可以为你自动执行这些步骤（创建示例文件并从索引移除配置），你已经授权我执行该操作。

## 扩展指引
- 新增提供商：在 `api/api_client.py` 扩展提供商表，补全 headers/payload/解析。
- 更换存储：实现 `core/ports/storage.py` 接口的适配器，即可替换 JSON 持久化。
- UI 组件化：在 `ui/` 目录新增组件并在 `app_ui.py` 挂载。

## 故障排查
- API 报错：确认 provider 选择与 API Key；必要时抓取响应文本查看错误详情。
- UI 卡顿：确保网络与重计算均在后台线程，主线程只做渲染与事件处理。

## 安全与提交
- 请勿提交真实密钥；提交前可在 `config/config.json` 留空或使用占位符。

---

需要我帮你初始化 Git 仓库、生成 `.gitignore` 或推送到 GitHub，请告诉我。
