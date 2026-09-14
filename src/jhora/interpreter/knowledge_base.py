"""Knowledge base — full-text search over books/articles using SQLite FTS5."""

import os
from pathlib import Path
from typing import List, Optional

from jhora.core.database import get_db

BOOKS_DIR = Path(__file__).resolve().parents[3] / "docs" / "books" / "extracted"


class KnowledgeBase:
    def __init__(self, books_dir: Optional[Path] = None):
        self._db = get_db()
        if books_dir is not None:
            self._load_on_demand(books_dir)
        else:
            # Repo extracts first, then the user's own books folder so
            # pip/frozen installs can grow a library too.
            self._load_on_demand(BOOKS_DIR)
            try:
                from jhora.paths import user_books_dir
                user_dir = user_books_dir()
                if user_dir.is_dir():
                    self._load_on_demand(user_dir)
            except Exception:
                pass

    def import_files(self, paths) -> dict:
        """Copy user-supplied .txt books into the personal library and load.

        Only plain text is accepted — copyright stays the user's own files.
        Returns {"added": [...], "skipped": [...]} of source names.
        """
        from jhora.paths import user_books_dir
        dest = user_books_dir()
        dest.mkdir(parents=True, exist_ok=True)
        added, skipped = [], []
        for raw in paths:
            src = Path(raw)
            if src.suffix.lower() != ".txt" or not src.is_file():
                skipped.append(f"{src.name} (not a .txt file)")
                continue
            target = dest / src.name
            if target.exists():
                skipped.append(f"{src.name} (already imported)")
                continue
            try:
                target.write_bytes(src.read_bytes())
                added.append(target.stem)
            except Exception as e:
                skipped.append(f"{src.name} ({e})")
        if added:
            self._load_on_demand(dest)
        return {"added": added, "skipped": skipped}

    def _load_on_demand(self, books_dir: Path):
        """Import text files into the database if not already loaded.

        The FTS reindex + commits run only when new books were actually
        added — previously every construction paid a full rebuild.
        """
        if not books_dir.exists():
            return
        existing = {
            row[0] for row in
            self._db.execute("SELECT source_name FROM knowledge_texts").fetchall()
        }
        added = False
        for f in sorted(books_dir.glob("*.txt")):
            name = f.stem.replace("_", " ").replace(".pdf", "").title()
            if name in existing:
                continue
            content = f.read_text(encoding="utf-8", errors="replace")
            self._db.execute(
                "INSERT INTO knowledge_texts (source_name, content, char_count) "
                "VALUES (?, ?, ?)",
                (name, content, len(content)),
            )
            added = True
        if not added:
            return
        self._db.commit()
        self._db.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
        self._db.commit()

    @property
    def loaded(self) -> int:
        row = self._db.execute("SELECT COUNT(*) FROM knowledge_texts").fetchone()
        return row[0]

    def list_sources(self) -> List[str]:
        return [
            row[0] for row in
            self._db.execute("SELECT source_name FROM knowledge_texts ORDER BY source_name")
        ]

    def search(self, query: str, max_results: int = 5, context_chars: int = 300) -> List[dict]:
        q = query.strip()
        if not q or len(q) < 2:
            return []
        # FTS5 MATCH is a query language (: " * ( ) ? ... crash or
        # misbehave). Reduce to plain word tokens (implicit AND) so any
        # user question is safe — a Guru question with a colon must never
        # take down the whole answer.
        import re
        tokens = re.findall(r"[A-Za-z0-9\u0080-\uffff]{2,}", q)[:12]
        if not tokens:
            return []
        q = " ".join(tokens)
        rows = self._db.execute(
            "SELECT k.source_name, k.content, "
            "snippet(knowledge_fts, 1, '', '', '...', 32) AS snippet, "
            "bm25(knowledge_fts, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0) AS rank "
            "FROM knowledge_fts f "
            "JOIN knowledge_texts k ON f.rowid = k.id "
            "WHERE knowledge_fts MATCH ? "
            "ORDER BY rank "
            "LIMIT ?",
            (q, max_results * 2),
        ).fetchall()

        results = []
        for row in rows:
            source = row["source_name"]
            content = row["content"]
            snippet = row["snippet"] or content[:context_chars]
            results.append({
                "source": source,
                "excerpt": snippet[:500],
                "score": float(row["rank"] or 0),
            })
        results.sort(key=lambda r: r["score"])
        return results[:max_results]

    def get_source(self, title: str) -> Optional[str]:
        row = self._db.execute(
            "SELECT content FROM knowledge_texts WHERE source_name = ?",
            (title,),
        ).fetchone()
        return row[0] if row else None

    def topics(self) -> List[str]:
        topics = set()
        keywords = [
            "dasa", "varga", "yoga", "graha", "rasi", "bhava", "lagna",
            "shadbala", "ashtakavarga", "tajaka", "transit", "remedy",
            "muhurta", "matchmaking", "prasna", "nakshatra", "karaka",
        ]
        for row in self._db.execute("SELECT source_name FROM knowledge_texts"):
            title = row[0].lower()
            for kw in keywords:
                if kw in title:
                    topics.add(kw)
        return sorted(topics)
