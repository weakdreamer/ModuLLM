"""SQLite-backed storage module with a drop-in compatible API."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from typing import Any, Dict, List, Optional


class Storage:
    """Session/message storage using SQLite (compatible with previous JSON API)."""

    def __init__(self, path: str | None = None):
        # 使用基于项目根目录的绝对路径，确保应用可移植
        _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.path = path or os.path.join(_PROJECT_ROOT, "storage", "data.db")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._enable_fk()
        self._init_db()

        # cache for compatibility with existing controller code
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._load_sessions_into_cache()

    def _enable_fk(self) -> None:
        try:
            self.conn.execute("PRAGMA foreign_keys = ON;")
        except Exception:
            pass

    def _init_db(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                draft TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS prompts (
                name TEXT PRIMARY KEY,
                role TEXT NOT NULL DEFAULT 'system',
                content TEXT NOT NULL
            );
            """
        )
        self.conn.commit()
        self._ensure_default_prompts()
        # 如果 sessions 为空，尝试从 legacy JSON（storage/data.json）导入示例会话
        cur = self.conn.execute("SELECT COUNT(1) FROM sessions")
        try:
            count = cur.fetchone()[0]
        except Exception:
            count = 0
        if count == 0:
            self._seed_from_json()

    def _ensure_default_prompts(self) -> None:
        cur = self.conn.execute("SELECT COUNT(1) FROM prompts")
        count = cur.fetchone()[0]
        if count == 0:
            self.conn.execute(
                "INSERT INTO prompts (name, role, content) VALUES (?, ?, ?)",
                ("default", "system", "You are a helpful assistant."),
            )
            self.conn.commit()

    def _seed_from_json(self) -> None:
        """如果存在旧的 `storage/data.json`，将其中的会话导入到新建的 SQLite DB 中。"""
        json_path = os.path.join(os.path.dirname(self.path), "data.json")
        if not os.path.exists(json_path):
            return
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        sessions = data.get("sessions", {}) if isinstance(data, dict) else {}
        try:
            for sid, sess in sessions.items():
                title = sess.get("title", "")
                draft = sess.get("draft", "")
                # 插入会话（如果不存在）
                self.conn.execute(
                    "INSERT OR IGNORE INTO sessions (session_id, title, draft) VALUES (?, ?, ?)",
                    (sid, title, draft),
                )
                # 插入消息
                for m in sess.get("messages", []) or []:
                    self.conn.execute(
                        "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                        (
                            sid,
                            m.get("role", "assistant"),
                            m.get("content", ""),
                            m.get("timestamp", ""),
                        ),
                    )
            self.conn.commit()
        except Exception:
            # 容错：若导入过程中出错，回滚以保持 DB 一致性
            try:
                self.conn.rollback()
            except Exception:
                pass

    def _load_sessions_into_cache(self) -> None:
        self.sessions = {}
        cur = self.conn.execute("SELECT session_id, title, draft FROM sessions")
        for row in cur.fetchall():
            self.sessions[row["session_id"]] = {
                "session_id": row["session_id"],
                "title": row["title"],
                "draft": row["draft"] or "",
                "messages": [],
            }

        # load messages grouped by session
        cur = self.conn.execute(
            "SELECT session_id, role, content, timestamp FROM messages ORDER BY id ASC"
        )
        for row in cur.fetchall():
            sess = self.sessions.get(row["session_id"])
            if not sess:
                continue
            sess.setdefault("messages", []).append(
                {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                }
            )

    def save(self) -> None:
        """Persist session metadata (title/draft) from cache to DB."""
        for sess in self.sessions.values():
            sid = sess.get("session_id")
            self.conn.execute(
                """
                INSERT INTO sessions (session_id, title, draft)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    title=excluded.title,
                    draft=excluded.draft
                """,
                (sid, sess.get("title", ""), sess.get("draft", "")),
            )
            # sync messages for this session to reflect any in-memory edits (e.g., deletions)
            self.conn.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
            msgs = sess.get("messages", []) or []
            for m in msgs:
                self.conn.execute(
                    "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                    (sid, m.get("role", "assistant"), m.get("content", ""), m.get("timestamp", "")),
                )
        self.conn.commit()

    def create_session(self, title: str = "New Session") -> str:
        sid = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO sessions (session_id, title, draft) VALUES (?, ?, '')",
            (sid, title),
        )
        self.conn.commit()
        self.sessions[sid] = {"session_id": sid, "title": title, "draft": "", "messages": []}
        return sid

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [
            {"session_id": s["session_id"], "title": s.get("title", "")}
            for s in self.sessions.values()
        ]

    def get_session(self, session_id: str) -> Dict[str, Any]:
        sess = self.sessions.get(session_id)
        if sess:
            return sess
        # fallback to empty session shape
        return {"session_id": session_id, "title": "", "messages": [], "draft": ""}

    def append_message(self, session_id: str, role: str, content: str) -> None:
        import datetime

        if session_id not in self.sessions:
            session_id = self.create_session("Auto")
        ts = datetime.datetime.now(datetime.UTC).isoformat()
        self.conn.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, ts),
        )
        self.conn.commit()
        self.sessions[session_id]["messages"].append({"role": role, "content": content, "timestamp": ts})

    def delete_session(self, session_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        self.conn.commit()
        removed = cur.rowcount > 0
        if removed:
            self.sessions.pop(session_id, None)
        return removed

    def clear_all_sessions(self) -> None:
        self.conn.execute("DELETE FROM sessions")
        self.conn.execute("DELETE FROM messages")
        self.conn.commit()
        self.sessions = {}

    def rename_session(self, session_id: str, new_title: str) -> bool:
        cur = self.conn.execute(
            "UPDATE sessions SET title = ? WHERE session_id = ?", (new_title, session_id)
        )
        self.conn.commit()
        if cur.rowcount > 0:
            if session_id in self.sessions:
                self.sessions[session_id]["title"] = new_title
            return True
        return False

    # Prompt management (DB-backed, PromptPort-compatible helpers)
    def list_prompts(self) -> List[Dict[str, str]]:
        cur = self.conn.execute("SELECT name, role, content FROM prompts ORDER BY name ASC")
        return [
            {"name": row["name"], "role": row["role"], "content": row["content"]}
            for row in cur.fetchall()
        ]

    def get_prompt(self, name: str) -> Optional[Dict[str, str]]:
        cur = self.conn.execute(
            "SELECT name, role, content FROM prompts WHERE name = ?", (name,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"name": row["name"], "role": row["role"], "content": row["content"]}

    def upsert_prompt(self, name: str, role: str, content: str) -> None:
        self.conn.execute(
            """
            INSERT INTO prompts (name, role, content)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                role=excluded.role,
                content=excluded.content
            """,
            (name, role, content),
        )
        self.conn.commit()

    def delete_prompt(self, name: str) -> bool:
        cur = self.conn.execute("DELETE FROM prompts WHERE name = ?", (name,))
        self.conn.commit()
        return cur.rowcount > 0


__all__ = ["Storage"]
