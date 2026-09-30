"""Tests for content-hash book refresh and v1→v2 migration."""
import sqlite3

from jhora.interpreter.knowledge_base import KnowledgeBase


def _write_book(path, text):
    path.write_text(text, encoding="utf-8")
    return path


class TestRefresh:
    def test_edited_file_refreshes_text_fts_and_chunks(self, tmp_path):
        books = tmp_path / "books"
        books.mkdir()
        _write_book(books / "tome.txt", "Jupiter dasha effects are mild here")
        kb = KnowledgeBase(books)
        assert kb.search("Jupiter dasha")[0]["source"] == "Tome"
        # A stale embedding chunk for this book must die on refresh.
        kb._db.execute(
            "CREATE TABLE IF NOT EXISTS textbook_chunks (id INTEGER PRIMARY "
            "KEY AUTOINCREMENT, source_name TEXT, chunk_index INTEGER, "
            "content TEXT, embedding BLOB)")
        kb._db.execute(
            "INSERT INTO textbook_chunks (source_name, chunk_index, content)"
            " VALUES ('Tome', 0, 'stale')");
        kb._db.commit()

        _write_book(books / "tome.txt", "Saturn sade sati brings trials here")
        kb2 = KnowledgeBase(books)
        hits = kb2.search("sade sati trials")
        assert hits and hits[0]["source"] == "Tome"
        assert kb2.search("Jupiter dasha mild") == [] or all(
            "mild here" not in h["excerpt"] for h in kb2.search("Jupiter dasha mild"))
        assert kb2._db.execute(
            "SELECT COUNT(*) FROM textbook_chunks WHERE source_name='Tome'"
        ).fetchone()[0] == 0

    def test_unchanged_file_costs_no_writes(self, tmp_path):
        books = tmp_path / "books"
        books.mkdir()
        _write_book(books / "tome.txt", "Jupiter dasha effects are mild here")
        kb = KnowledgeBase(books)
        kb._db.execute(
            "CREATE TABLE IF NOT EXISTS textbook_chunks (id INTEGER PRIMARY "
            "KEY AUTOINCREMENT, source_name TEXT, chunk_index INTEGER, "
            "content TEXT, embedding BLOB)")
        kb._db.execute(
            "INSERT INTO textbook_chunks (source_name, chunk_index, content)"
            " VALUES ('Tome', 0, 'keep me')");
        kb._db.commit()
        before = kb._db.execute(
            "SELECT content FROM knowledge_texts WHERE source_name='Tome'"
        ).fetchone()[0]

        kb2 = KnowledgeBase(books)  # same bytes: must skip everything
        assert kb2._db.execute(
            "SELECT content FROM knowledge_texts WHERE source_name='Tome'"
        ).fetchone()[0] == before
        assert kb2._db.execute(
            "SELECT COUNT(*) FROM textbook_chunks WHERE source_name='Tome'"
        ).fetchone()[0] == 1


class TestMigration:
    def test_v1_db_grows_hash_column(self, tmp_path):
        from jhora.core import database as db
        target = tmp_path / "v1.db"
        conn = sqlite3.connect(str(target))
        conn.executescript("""
            CREATE TABLE schema_version (version INTEGER);
            INSERT INTO schema_version VALUES (1);
            CREATE TABLE knowledge_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                char_count INTEGER NOT NULL DEFAULT 0,
                loaded_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            INSERT INTO knowledge_texts (source_name, content, char_count)
            VALUES ('Old Tome', 'ancient words here', 18);
            CREATE VIRTUAL TABLE knowledge_fts USING fts5(
                source_name, content,
                content='knowledge_texts', content_rowid='id'
            );
        """)
        conn.commit()
        conn.close()
        db.set_db_path(target)
        conn2 = db.get_db()
        cols = {row[1] for row in conn2.execute("PRAGMA table_info(knowledge_texts)")}
        assert "content_hash" in cols
        assert conn2.execute("SELECT version FROM schema_version").fetchone()[0] == 2
        # NULL hash counts as changed: next load refreshes the row.
        books = tmp_path / "books"
        books.mkdir()
        _write_book(books / "old_tome.txt", "revised words here")
        kb = KnowledgeBase(books)
        assert kb.search("revised words")[0]["source"] == "Old Tome"
