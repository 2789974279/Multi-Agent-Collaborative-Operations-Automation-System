from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from core.schemas import AgentResult, TaskInput


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class Repository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    audience TEXT NOT NULL,
                    constraints TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    agent TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );
                """
            )

    def create_task(self, task: TaskInput) -> dict[str, Any]:
        now = utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks(title, scenario, objective, audience, constraints, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task.title, task.scenario, task.objective, task.audience, task.constraints, "pending", now, now),
            )
            task_id = int(cursor.lastrowid)
        self.add_event(task_id, "system", "task_created", "任务已创建", {"scenario": task.scenario})
        return self.get_task(task_id) or {}

    def list_tasks(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return [self.serialize_task(row) for row in rows]

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self.serialize_task(row) if row else None

    def update_task_status(self, task_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, utc_now(), task_id),
            )

    def save_task_result(self, task_id: int, status: str, result: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, result_json = ?, updated_at = ? WHERE id = ?",
                (status, json.dumps(result, ensure_ascii=False), utc_now(), task_id),
            )

    def add_event(self, task_id: int, agent: str, event_type: str, message: str, payload: dict[str, Any] | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO events(task_id, agent, event_type, message, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    agent,
                    event_type,
                    message,
                    json.dumps(payload or {}, ensure_ascii=False),
                    utc_now(),
                ),
            )

    def list_events(self, task_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE task_id = ? ORDER BY id ASC",
                (task_id,),
            ).fetchall()
        return [self.serialize_event(row) for row in rows]

    def serialize_task(self, row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json") or "{}")
        return item

    def serialize_event(self, row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json") or "{}")
        return item


