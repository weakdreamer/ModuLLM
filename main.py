"""程序入口：组装模块并运行 UI。"""
from config import load_config, get_config
from storage import Storage
from api import ApiClient
from controller import Controller
from ui import AppUI
from prompt import DbPromptManager
from comm import WebSocketComm


def main():
    cfg = load_config()
    storage = Storage()
    client = ApiClient(cfg)
    prompt_manager = DbPromptManager(storage)
    comm = None
    if cfg.get("comm_enabled"):
        comm = WebSocketComm(
            cfg.get("comm_server_url", "ws://localhost:8765"),
            cfg.get("comm_auth_key", ""),
        )
    ui = AppUI(None)
    controller = Controller(ui, storage, client, cfg, prompt_manager, comm)
    ui.c = controller
    ui.run()


if __name__ == "__main__":
    main()
