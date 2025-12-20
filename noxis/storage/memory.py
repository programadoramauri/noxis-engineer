from __future__ import annotations

import sqlite3
import json
from pathlib import Path

class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    command TEXT NOT NULL,
                    payload_json TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_explanations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                prompt_hash TEXT NOT NULL,
                response TEXT NOT NULL
                );
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_state(
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                """
            )
            conn.commit()

    def record_run(self, command:str, payload: dict | None = None) -> None:
        payload_json = json.dumps(payload or {}, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO runs (command, payload_json) VALUES (?, ?)",
                (command, payload_json),
            )

            conn.commit()

    def record_ai_explanation(self, prompt_hash: str, response: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ai_explanations (prompt_hash, response)
                VALUES (?, ?)
                """,
                (prompt_hash, response),
            )
            conn.commit()

    def set_state(self, key:str, value: dict) -> None:
        import json
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO project_state (key, value_json, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = datetime('now');
                """,
                (key, json.dumps(value, ensure_ascii=False)),
            )
            conn.commit()

    def get_state(self, key: str) -> dict | None:
        import json
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value_json FROM project_state WHERE key = ?",
                (key,),
            ).fetchone()

        if not row:
            return None

        return json.loads(row[0])
