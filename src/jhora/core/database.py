"""Unified SQLite database for Jhora — atlas, knowledge, charts, preferences.

Opens `data/jhora.db` relative to the project root. Creates all tables on first
access and supports schema migrations.
"""

import json
import sqlite3
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_NAME = "jhora.db"
SCHEMA_VERSION = 2

_db_path: Optional[Path] = None
_connections: Dict[int, sqlite3.Connection] = {}
_lock = threading.Lock()


def _find_db() -> Path:
    """Locate or create the database file path."""
    if getattr(sys, "frozen", False):
        # Installed apps cannot write beside the executable: use the
        # per-user data directory (APPDATA / Application Support / XDG).
        from jhora.paths import user_data_dir
        p = user_data_dir() / DB_NAME
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    candidates = [
        Path.cwd() / "data" / DB_NAME,
        Path(__file__).resolve().parents[4] / "data" / DB_NAME,
        Path(__file__).resolve().parents[3] / "data" / DB_NAME,
    ]
    for p in candidates:
        if p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            _seed_working_copy(p)
            return p
    p = candidates[0]
    p.parent.mkdir(parents=True, exist_ok=True)
    _seed_working_copy(p)
    return p


def _seed_working_copy(p: Path):
    """First run copies the tracked seed DB to the working copy.

    The seed (schema + cities atlas, no personal content) is tracked;
    the working copy is gitignored. Existing working copies — including
    every current checkout — are never touched.
    """
    seed = p.with_name("jhora.seed.db")
    if not p.exists() and seed.is_file():
        import shutil
        shutil.copy2(seed, p)


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


def get_preference(key: str, default: str = "") -> str:
    """Read a user preference (empty string when unset)."""
    try:
        row = get_db().execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default
    except Exception:
        return default


def set_preference(key: str, value: str) -> None:
    """Persist a user preference (best-effort, never raises)."""
    try:
        get_db().execute(
            "INSERT INTO preferences (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        get_db().commit()
    except Exception:
        pass


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

    # Ensure AI chat thread tables exist — older databases predate them.
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_threads'"
    )
    if cur.fetchone() is None:
        _create_chat_tables(conn)
        conn.commit()

    # Ensure AI guru thread tables exist — older databases predate them.
    # Separate tables from chat_threads by design: the two features diverge
    # freely and share only the connection helper.
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='guru_threads'"
    )
    if cur.fetchone() is None:
        _create_guru_tables(conn)
        conn.commit()

    _run_migrations(conn)


def _run_migrations(conn: sqlite3.Connection):
    """Version-gated migrations (fresh DBs already stamp SCHEMA_VERSION)."""
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    version = row[0] if row else SCHEMA_VERSION
    if version < 2:
        _migrate_to_2(conn)
        conn.execute("UPDATE schema_version SET version = 2")
        conn.commit()


def _migrate_to_2(conn: sqlite3.Connection):
    """Add the book content hash (NULL = refresh on next load)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(knowledge_texts)")}
    if "content_hash" not in cols:
        conn.execute("ALTER TABLE knowledge_texts ADD COLUMN content_hash TEXT")


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
    _create_chat_tables(conn)
    _create_guru_tables(conn)


def _create_chat_tables(conn: sqlite3.Connection):
    """Create AI chat thread tables (owned by the AI Chat tab; the Guru tab
    owns its own parallel tables so the two features diverge freely)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_fp TEXT NOT NULL,
            title TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            messages_json TEXT NOT NULL DEFAULT '[]'
        );
        CREATE INDEX IF NOT EXISTS idx_chat_threads_chart
            ON chat_threads(chart_fp, updated_at);
    """)


def _create_guru_tables(conn: sqlite3.Connection):
    """Create AI guru thread tables (owned by the Guru tab; parallel to —
    never shared with — the chat tab's tables)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS guru_threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_fp TEXT NOT NULL,
            title TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            messages_json TEXT NOT NULL DEFAULT '[]'
        );
        CREATE INDEX IF NOT EXISTS idx_guru_threads_chart
            ON guru_threads(chart_fp, updated_at);
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
            content_hash TEXT,
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
    _create_chat_tables(conn)
    _create_guru_tables(conn)


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
