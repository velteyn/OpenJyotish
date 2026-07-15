"""Embedding-based semantic search for the Vedic textbook corpus.

Uses Ollama's embedding API to generate vectors, stores them in SQLite,
and performs cosine-similarity search. Falls back to FTS5 if Ollama not available.
"""

import json
import struct
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from jhora.core.database import get_db


EMBEDDING_DIM = 768  # Typical for nomic-embed-text / all-minilm
CHUNK_SIZE = 500     # Characters per chunk
CHUNK_OVERLAP = 100  # Overlap between chunks


def _ollama_embed(text: str, base_url: str = "http://localhost:11434") -> Optional[List[float]]:
    """Get embedding vector from Ollama API."""
    import requests
    try:
        resp = requests.post(
            f"{base_url}/api/embed",
            json={"model": "nomic-embed-text", "input": text},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings", [])
        return embeddings[0] if embeddings else None
    except Exception:
        return None


def _pack_vector(vec: List[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack_vector(blob: bytes) -> np.ndarray:
    count = len(blob) // 4
    return np.array(struct.unpack(f"{count}f", blob), dtype=np.float32)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


class EmbeddingStore:
    """Manage chunked textbook storage with vector embeddings."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.db = get_db()
        self.base_url = base_url
        self._ensure_tables()

    def _ensure_tables(self):
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS textbook_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_source ON textbook_chunks(source_name);
        """)
        self.db.commit()

    def build(self, books_dir: str = None):
        """Chunk all books, embed them, store in DB."""
        if books_dir is None:
            books_dir = Path(__file__).resolve().parents[3] / "docs" / "books" / "extracted"
        books_dir = Path(books_dir)
        if not books_dir.exists():
            print(f"Books dir not found: {books_dir}")
            return 0

        count = self.db.execute("SELECT COUNT(*) FROM textbook_chunks").fetchone()[0]
        if count > 0:
            print(f"Already have {count} chunks — use rebuild=True to recreate")
            return count

        total = 0
        for txt_file in sorted(books_dir.glob("*.txt")):
            name = txt_file.stem.replace("_", " ").replace(".pdf", "").title()
            text = txt_file.read_text(encoding="utf-8", errors="replace")
            chunks = self._chunk_text(text)
            print(f"  {name}: {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                emb = _ollama_embed(chunk, self.base_url)
                blob = _pack_vector(emb) if emb else None
                self.db.execute(
                    "INSERT INTO textbook_chunks (source_name, chunk_index, content, embedding) "
                    "VALUES (?, ?, ?, ?)",
                    (name, i, chunk, blob),
                )
                total += 1
                if total % 10 == 0:
                    self.db.commit()
                    print(f"    {total} chunks embedded...", end="\r")
        self.db.commit()
        print(f"\n  Done: {total} chunks stored")
        return total

    def _chunk_text(self, text: str) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            # Try to break at sentence boundary
            if end < len(text):
                for sep in [". ", "! ", "? ", "\n\n", "\n", " "]:
                    pos = text.rfind(sep, start, end)
                    if pos > start + CHUNK_SIZE // 2:
                        end = pos + len(sep.rstrip())
                        break
            chunk = text[start:end].strip()
            if len(chunk) > 50:
                chunks.append(chunk)
            start = end - CHUNK_OVERLAP
        return chunks

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Semantic search with cosine similarity, falling back to FTS5."""
        # Try embedding search first
        query_emb = _ollama_embed(query, self.base_url)
        if query_emb is not None:
            return self._vector_search(query_emb, top_k)
        # Fallback to FTS5 full-text search
        return self._fts_search(query, top_k)

    def _vector_search(self, query_vec: List[float], top_k: int) -> List[dict]:
        q = np.array(query_vec, dtype=np.float32)
        results = []
        for row in self.db.execute(
            "SELECT id, source_name, content, embedding FROM textbook_chunks "
            "WHERE embedding IS NOT NULL"
        ).fetchall():
            if row["embedding"] is None:
                continue
            vec = _unpack_vector(row["embedding"])
            sim = _cosine_similarity(q, vec)
            results.append({
                "id": row["id"],
                "source": row["source_name"],
                "content": row["content"],
                "score": sim,
            })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def _fts_search(self, query: str, top_k: int) -> List[dict]:
        from jhora.interpreter.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        kb_results = kb.search(query, max_results=top_k, context_chars=500)
        return [
            {"source": r["source"], "content": r["excerpt"], "score": r["score"]}
            for r in kb_results
        ]

    @property
    def chunk_count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM textbook_chunks").fetchone()[0]

    @property
    def has_embeddings(self) -> bool:
        row = self.db.execute(
            "SELECT COUNT(*) FROM textbook_chunks WHERE embedding IS NOT NULL"
        ).fetchone()
        return row[0] > 0
