"""Unified SQLite database for Jhora — atlas, knowledge, charts, preferences.

Opens `data/jhora.db` relative to the project root. Creates all tables on first
access and supports schema migrations.
"""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_NAME = "jhora.db"
SCHEMA_VERSION = 1

_db_path: Optional[Path] = None
_connections: Dict[int, sqlite3.Connection] = {}
_lock = threading.Lock()


def _find_db() -> Path:
    """Locate or create the database file path."""
    candidates = [
        Path.cwd() / "data" / DB_NAME,
        Path(__file__).resolve().parents[4] / "data" / DB_NAME,
        Path(__file__).resolve().parents[3] / "data" / DB_NAME,
    ]
    for p in candidates:
        if p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            return p
    p = candidates[0]
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def set_db_path(path: str | Path):
    """Override the database path (for testing)."""
    global _db_path, _connections
    with _lock:
        _db_path = Path(path)
        for conn in _connections.values():
            try:
                conn.close()
            except Exception:
                pass
        _connections.clear()


def get_db() -> sqlite3.Connection:
    """Return a thread-local database connection (auto-creates tables)."""
    global _db_path
    tid = threading.get_ident()
    with _lock:
        if tid in _connections:
            return _connections[tid]
        if _db_path is None:
            _db_path = _find_db()
        conn = sqlite3.connect(str(_db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _connections[tid] = conn
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection):
    """Create tables if they don't exist, run migrations."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cur.fetchone() is None:
        _create_all(conn)
        conn.execute("INSERT INTO schema_version VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
        return

    # Ensure charts/preferences tables exist — the prebuilt textbook DB has
    # schema_version but lacks these application tables.
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='charts'"
    )
    if cur.fetchone() is None:
        _create_application_tables(conn)
        conn.commit()


def _create_application_tables(conn: sqlite3.Connection):
    """Create only the charts, chart_planets, and preferences tables."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            day INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            time_hours REAL NOT NULL,
            tz_offset REAL NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            ayanamsa TEXT DEFAULT 'lahiri',
            city TEXT DEFAULT '',
            country TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS chart_planets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_id INTEGER NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
            graha INTEGER NOT NULL,
            longitude REAL NOT NULL,
            latitude REAL NOT NULL DEFAULT 0,
            speed REAL DEFAULT 0,
            is_retrograde INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_chart_planets_chart ON chart_planets(chart_id);

        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)


def _create_all(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE schema_version (version INTEGER);

        -- Atlas: city search
        CREATE TABLE cities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            ascii_name TEXT NOT NULL,
            country TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            tz_offset REAL NOT NULL
        );
        CREATE VIRTUAL TABLE cities_fts USING fts5(
            name, ascii_name, country,
            content='cities', content_rowid='id'
        );

        -- Knowledge base: books/articles
        CREATE TABLE knowledge_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            char_count INTEGER NOT NULL DEFAULT 0,
            loaded_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE VIRTUAL TABLE knowledge_fts USING fts5(
            source_name, content,
            content='knowledge_texts', content_rowid='id'
        );

        -- Saved charts
        CREATE TABLE charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            day INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            time_hours REAL NOT NULL,
            tz_offset REAL NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            ayanamsa TEXT DEFAULT 'lahiri',
            city TEXT DEFAULT '',
            country TEXT DEFAULT ''
        );
        CREATE TABLE chart_planets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_id INTEGER NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
            graha INTEGER NOT NULL,
            longitude REAL NOT NULL,
            latitude REAL NOT NULL DEFAULT 0,
            speed REAL DEFAULT 0,
            is_retrograde INTEGER DEFAULT 0
        );
        CREATE INDEX idx_chart_planets_chart ON chart_planets(chart_id);

        -- User preferences
        CREATE TABLE preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)


# ---- Query helpers ----

def close_all():
    """Close all connections (useful for testing teardown)."""
    with _lock:
        for conn in _connections.values():
            try:
                conn.close()
            except Exception:
                pass
        _connections.clear()
