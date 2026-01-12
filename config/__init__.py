"""配置模块：读/写 JSON 配置，提供简单的 get/set 接口。"""
import json
import os
from typing import Dict, Any

_CFG: Dict[str, Any] = {}
# 使用基于项目根目录的绝对路径，确保应用可移植
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH = os.path.join(_PROJECT_ROOT, "config", "config.json")
_LOADED = False

# 默认配置，用于缺失字段补全
DEFAULT_CFG: Dict[str, Any] = {
    "current_model": "",
    "models": {},
    "max_history_messages": 10,
    "timeout": 60,
    "input_height": 4,
    "window_width": 1000,
    "window_height": 700,
    "theme": "light",
    "comm_enabled": False,
    "comm_server_url": "ws://localhost:8765",
    "comm_auth_key": "",
    "comm_use_remote_model": False,
}


def load_config(path: str | None = None) -> Dict[str, Any]:
    """加载配置文件到内存缓存，若不存在则使用默认值并写入文件。"""
    global _CFG, _PATH, _LOADED
    if _LOADED:
        return _CFG
    if path:
        _PATH = path
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    if os.path.exists(_PATH):
        with open(_PATH, "r", encoding="utf-8") as f:
            _CFG = json.load(f)
        # 补全缺失的默认字段，保持向后兼容
        for k, v in DEFAULT_CFG.items():
            _CFG.setdefault(k, v)
        save_config(_CFG)
    else:
        # 如果不存在 config.json，优先使用同目录下的 config.example.json 作为初始配置
        example_path = os.path.join(os.path.dirname(_PATH), "config.example.json")
        if os.path.exists(example_path):
            try:
                with open(example_path, "r", encoding="utf-8") as f:
                    _CFG = json.load(f)
            except Exception:
                _CFG = dict(DEFAULT_CFG)
        else:
            _CFG = dict(DEFAULT_CFG)

        # 补全默认字段并持久化为正式配置文件
        for k, v in DEFAULT_CFG.items():
            _CFG.setdefault(k, v)
        save_config(_CFG)
    _LOADED = True
    return _CFG


def save_config(cfg: Dict[str, Any] | None = None, path: str | None = None) -> None:
    """持久化当前配置到 JSON 文件。"""
    global _CFG, _PATH
    if path:
        _PATH = path
    data = cfg if cfg is not None else _CFG
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_config() -> Dict[str, Any]:
    """返回内存中的配置引用（直接可读写）。"""
    if not _LOADED:
        load_config()
    return _CFG


def set_config(key: str, value: Any) -> None:
    """设置单个配置项并持久化。"""
    _CFG[key] = value
    save_config()


def save_model(name: str, model_config: Dict[str, Any]) -> None:
    """保存模型配置"""
    if "models" not in _CFG:
        _CFG["models"] = {}
    _CFG["models"][name] = model_config
    save_config()


def get_model(name: str) -> Dict[str, Any] | None:
    """获取模型配置"""
    return _CFG.get("models", {}).get(name)


def get_all_models() -> Dict[str, Dict[str, Any]]:
    """获取所有模型配置"""
    return _CFG.get("models", {})


def delete_model(name: str) -> None:
    """删除模型配置"""
    if "models" in _CFG and name in _CFG["models"]:
        del _CFG["models"][name]
        save_config()


def set_current_model(name: str) -> None:
    """设置当前使用的模型"""
    _CFG["current_model"] = name
    save_config()


def get_current_model() -> str:
    """获取当前使用的模型名称"""
    return _CFG.get("current_model", "")


__all__ = ["load_config", "save_config", "get_config", "set_config", "save_model", "get_model", "get_all_models", "delete_model", "set_current_model", "get_current_model"]
