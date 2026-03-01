"""
SQLite database layer.

Schema:
  courses         — dummy course catalog
  course_modules  — modules belonging to catalog courses
  pipelines       — pipeline run state (brief + nodes stored as JSON)
  decision_log    — audit trail of every agent action

All async operations use aiosqlite. Schema initialization is synchronous
(called once at startup via init_db_sync).
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiosqlite

from config import DB_PATH


# ─── Schema Init ──────────────────────────────────────────────────────────────


def init_db_sync() -> None:
    """Create all tables if they don't exist. Runs synchronously at startup."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            duration    TEXT    NOT NULL,
            audience    TEXT    NOT NULL,
            topic_area  TEXT    NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS course_modules (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id        INTEGER NOT NULL REFERENCES courses(id),
            title            TEXT    NOT NULL,
            description      TEXT,
            topics           TEXT    NOT NULL DEFAULT '[]',
            duration_minutes INTEGER,
            order_index      INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS pipelines (
            id           TEXT PRIMARY KEY,
            brief_json   TEXT NOT NULL,
            nodes_json   TEXT NOT NULL DEFAULT '[]',
            status       TEXT NOT NULL DEFAULT 'created',
            created_at   TEXT NOT NULL,
            started_at   TEXT,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS decision_log (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp      TEXT    NOT NULL,
            pipeline_id    TEXT,
            node_id        TEXT    NOT NULL,
            node_type      TEXT    NOT NULL,
            action         TEXT    NOT NULL,
            reasoning      TEXT    NOT NULL,
            confidence     REAL    NOT NULL,
            autonomy_level TEXT    NOT NULL,
            human_override INTEGER NOT NULL DEFAULT 0,
            human_decision TEXT
        );
        """
    )
    conn.commit()
    conn.close()


# ─── Catalog ──────────────────────────────────────────────────────────────────


def catalog_is_seeded_sync() -> bool:
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    conn.close()
    return count > 0


async def get_all_courses() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row

        async with db.execute("SELECT * FROM courses ORDER BY id") as cur:
            courses = [dict(r) for r in await cur.fetchall()]

        for course in courses:
            async with db.execute(
                "SELECT * FROM course_modules WHERE course_id = ? ORDER BY order_index",
                (course["id"],),
            ) as cur:
                modules = [dict(r) for r in await cur.fetchall()]
            for m in modules:
                m["topics"] = json.loads(m["topics"])
            course["modules"] = modules

        return courses


# ─── Pipelines ────────────────────────────────────────────────────────────────


async def create_pipeline(pipeline_id: str, brief_json: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO pipelines (id, brief_json, nodes_json, status, created_at)
            VALUES (?, ?, '[]', 'created', ?)
            """,
            (pipeline_id, brief_json, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_pipeline(pipeline_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        async with db.execute(
            "SELECT * FROM pipelines WHERE id = ?", (pipeline_id,)
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            return None

        result = dict(row)
        result["brief"] = json.loads(result["brief_json"])
        result["nodes"] = json.loads(result["nodes_json"])
        return result


async def update_pipeline_nodes(pipeline_id: str, nodes_json: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE pipelines SET nodes_json = ? WHERE id = ?",
            (nodes_json, pipeline_id),
        )
        await db.commit()


async def update_pipeline_status(
    pipeline_id: str,
    status: str,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        if started_at:
            await db.execute(
                "UPDATE pipelines SET status = ?, started_at = ? WHERE id = ?",
                (status, started_at, pipeline_id),
            )
        elif completed_at:
            await db.execute(
                "UPDATE pipelines SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, pipeline_id),
            )
        else:
            await db.execute(
                "UPDATE pipelines SET status = ? WHERE id = ?",
                (status, pipeline_id),
            )
        await db.commit()


# ─── Decision Log ─────────────────────────────────────────────────────────────


async def log_decision(
    node_id: str,
    node_type: str,
    action: str,
    reasoning: str,
    confidence: float,
    autonomy_level: str,
    pipeline_id: Optional[str] = None,
    human_override: bool = False,
    human_decision: Optional[str] = None,
) -> int:
    """Insert a decision log entry and return its auto-generated id."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            INSERT INTO decision_log
                (timestamp, pipeline_id, node_id, node_type, action, reasoning,
                 confidence, autonomy_level, human_override, human_decision)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                pipeline_id,
                node_id,
                node_type,
                action,
                reasoning,
                confidence,
                autonomy_level,
                int(human_override),
                human_decision,
            ),
        ) as cur:
            row_id = cur.lastrowid
        await db.commit()
    return row_id


async def get_decision_log(pipeline_id: str) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        async with db.execute(
            """
            SELECT * FROM decision_log
            WHERE pipeline_id = ?
            ORDER BY timestamp DESC
            """,
            (pipeline_id,),
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]
