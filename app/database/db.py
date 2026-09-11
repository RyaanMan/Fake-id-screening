from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "screening.db"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_number TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                nationality TEXT,
                expiry TEXT,
                status TEXT NOT NULL,
                blacklisted INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                document_hash TEXT,
                risk_level TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def seed_demo_data() -> None:
    rows = [
        ("DEMO123456", "TEST PERSON", "IND", "2030-01-01", "ACTIVE", 0),
        ("BLOCK000001", "BLACKLIST DEMO", "IND", "2028-01-01", "BLACKLISTED", 1),
        ("EXPIRE00001", "EXPIRED DEMO", "IND", "2020-01-01", "EXPIRED", 0),
    ]
    with connect() as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO documents
            (document_number, name, nationality, expiry, status, blacklisted)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def find_document(document_number: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE document_number = ?",
            (document_number,),
        ).fetchone()
    return dict(row) if row else None


def log_action(
    username: str,
    role: str,
    action: str,
    document_hash: str | None,
    risk_level: str | None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO audit_log (username, role, action, document_hash, risk_level)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, role, action, document_hash, risk_level),
        )


def recent_audit(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
