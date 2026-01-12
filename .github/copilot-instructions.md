# AI Coding Agent Instructions for LLM Client Project

## Project Overview
This is a modular Python desktop application for interacting with multiple LLM APIs (Gemini, SiliconFlow, DeepSeek, Grok). It features a Tkinter GUI with session management, message history, and token tracking.

**最终实现的功能需考虑人性化和操作体验，而不是在操作者没有提到的地方不进行任何考虑**

## Architecture
- **MVC-like structure**: `controller/` coordinates `ui/`, `storage/`, and `api/` modules
- **Modular design**: Each feature in separate folders with `__init__.py`
- **Async API calls**: Uses threading + queue for non-blocking UI during API requests
- **JSON persistence**: Config in `config/config.json`, sessions in `storage/data.json`

## Key Components
- `main.py`: Entry point assembling modules
- `controller/controller.py`: Core logic, threading, message handling
- `ui/app_ui.py`: Main Tkinter window with modular sub-components
- `api/api_client.py`: Multi-provider API client with mock fallback
- `storage/__init__.py`: Session/message persistence
- `config/__init__.py`: Configuration management with migration

## Critical Workflows
- **Run app**: `python -m main.py` (not `python main.py`)
- **Test**: `pytest` (UI tests use Tkinter fixtures)
- **Mock mode**: App runs without API keys for testing
- **Async pattern**: API calls in background threads, results via queue to UI thread
- **Environment**: Always activate virtual environment before running commands (e.g., `conda activate myenv` or `venv\Scripts\activate`)
- **Quick setup (Windows)**: `python -m venv .venv`; `.venv\Scripts\Activate.ps1`; `pip install -r requirements.txt`; `python -m main`; `pytest`

## Code Patterns
- **Message format**: `{"role": "user/assistant", "content": str, "timestamp": "ISO"}`
- **Context limiting**: Use `max_history_messages` from config to slice message history
- **UI updates**: Always in main thread; use `root.after(0, callback)` for thread-safe updates
- **Error handling**: Wrap API calls in try/except, return error strings for display
- **Threading**: `threading.Thread(target=func, daemon=True).start()` for background tasks

## Data & Message Contracts (Do Not Forget)
- **Message**: `{role: str, content: str, timestamp: ISO}` (ISO UTC recommended)
- **Session**: `{session_id: str, title: str, draft: str, messages: list[Message]}`
- **Comm payload** (for future comms): request `{type: "chat_request", session_id, messages, prompt, meta}`; reply `{type: "chat_reply", session_id, messages, reply, meta}`
- **Prompt template**: `{name: {"role": "system", "content": str}}`

## Ports (Interfaces) for Pluggable Modules
Defined in `core/ports/` using `Protocol`:
- `ModelClientPort.send_chat(messages, cfg=None) -> str`
- `PromptPort.get_system_prompt(name) -> Message | None`; `apply_prompt(messages, prompt_name) -> list[Message]`
- `StoragePort.list_sessions() -> list[SessionSummary]`; `get_session(id) -> Session`; `create_session(title) -> str`; `save_session(session)`; `append_message(session_id, role, content)`; `delete_session(id) -> bool`; `clear_all_sessions()`; `rename_session(id, new_title) -> bool`
- `CommPort.start|stop|send(target, payload)`; `on_message(handler)`
- `ConfigPort.load() -> dict`; `save(cfg)`

## Examples
- **Adding new provider**: Extend `ApiClient.PROVIDERS` dict with base_url, headers lambda, payload_format
- **UI component**: Subclass or create in `ui/`, integrate via callbacks (e.g., `on_select = lambda: ...`)
- **Config migration**: Check for old keys in `load_config()`, update and `save_config()`
- **Session operations**: Use `storage.Storage` methods, always call `save()` after changes

## Testing
- Unit tests for UI components in `tests/`
- Use `tk_root` fixture for Tkinter tests
- Mock API responses for integration tests

## Dependencies
- `requests` for HTTP
- `pytest` for testing
- `Pillow` for images (if used in UI)

## 语言
- 优先使用中文说明自己的行为

Avoid blocking the UI thread. Prefer modular additions over monolithic changes.