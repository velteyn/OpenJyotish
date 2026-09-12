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


def _looks_like_embedding(model_id: str) -> bool:
    low = (model_id or "").lower()
    return any(h in low for h in ("embed", "nomic", "bge", "gte-", "e5-"))
CHUNK_SIZE = 500     # Characters per chunk
CHUNK_OVERLAP = 100  # Overlap between chunks


def _get_embeddings_batch(texts: List[str], base_url: str,
                          provider: str, model: str = "") -> List[Optional[List[float]]]:
    """Get embeddings for multiple texts in one API call."""
    import requests
    try:
        if provider == "lmstudio":
            resp = requests.post(
                f"{base_url}/v1/embeddings",
                json={"model": model or "loaded", "input": texts},
                timeout=60,
            )
        else:
            resp = requests.post(
                f"{base_url}/api/embed",
                json={"model": model or "nomic-embed-text", "input": texts},
                timeout=60,
            )
        resp.raise_for_status()
        data = resp.json()
        if provider == "lmstudio":
            return [item["embedding"] for item in data["data"]]
        else:
            return data.get("embeddings", [])
    except Exception as e:
        err_msg = ""
        if 'resp' in locals() and hasattr(resp, 'text'):
            err_msg = f"{resp.status_code} - {resp.text}"
        else:
            err_msg = str(e)
            
        raise RuntimeError(
            f"Embedding failed! Make sure a dedicated TEXT EMBEDDING model "
            f"(like nomic-embed-text) is loaded in your AI server.\n\n"
            f"Details: {err_msg}"
        )


def _get_embedding(text: str, base_url: str = "http://localhost:11434",
                   provider: str = "ollama") -> Optional[List[float]]:
    """Get embedding vector from Ollama or LM Studio.

    Ollama:  POST /api/embed  {"model": "nomic-embed-text", "input": text}
    LM Studio: POST /v1/embeddings  {"model": "...", "input": text}
    """
    import requests
    try:
        if provider == "lmstudio":
            resp = requests.post(
                f"{base_url}/v1/embeddings",
                json={"model": "text-embedding-nomic-embed-text-v1.5",
                      "input": text},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
        else:  # ollama
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


def _detect_provider(provider: str, base_url: str) -> tuple:
    """Auto-detect which LLM server is running."""
    import requests

    if provider == "auto":
        if base_url:
            # An explicit URL wins: probe it instead of localhost so remote
            # servers (LAN, Tailscale) work instead of silently dropping to
            # ("none", "") and failing later with a bare '/api/embed'.
            try:
                r = requests.get(f"{base_url.rstrip('/')}/v1/models",
                                 timeout=3)
                if r.status_code == 200:
                    return ("lmstudio", base_url)
            except Exception:
                pass
            try:
                r = requests.get(f"{base_url.rstrip('/')}/api/tags",
                                 timeout=3)
                if r.status_code == 200:
                    return ("ollama", base_url)
            except Exception:
                pass
            return ("none", base_url)
        # Try Ollama first
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                return ("ollama", "http://localhost:11434")
        except Exception:
            pass
        # Try LM Studio
        try:
            r = requests.get("http://localhost:1234/v1/models", timeout=2)
            if r.status_code == 200:
                return ("lmstudio", "http://localhost:1234")
        except Exception:
            pass
        # Neither found — fall back to FTS5
        return ("none", "")

    # Explicit provider
    urls = {"ollama": "http://localhost:11434",
            "lmstudio": "http://localhost:1234"}
    return (provider, base_url or urls.get(provider, "http://localhost:11434"))


def embedding_model_status(base_url: str = "",
                           provider: str = "auto") -> dict:
    """Pre-flight check: is a text-embedding model available to use?

    Returns {"ok", "provider", "base_url", "model", "message", "howto"}.
    Callers must refuse to build (with a popup telling the user what to
    download) when ok is False instead of failing mid-build.
    """
    import requests
    prov, base = _detect_provider(provider, base_url)
    if prov == "none" or not base:
        return {
            "ok": False, "provider": prov, "base_url": base, "model": "",
            "message": "No AI server reachable.",
            "howto": ("Start one first:\n"
                      "  LM Studio: start the local server (Developer tab)\n"
                      "  Ollama: ollama serve"),
        }
    found = ""
    server_up = False
    try:
        if prov == "lmstudio":
            r = requests.get(f"{base.rstrip('/')}/v1/models", timeout=5)
            server_up = r.status_code == 200
            if server_up:
                for m in r.json().get("data", []):
                    if _looks_like_embedding(str(m.get("id", ""))):
                        found = str(m.get("id", ""))
                        break
        else:
            r = requests.get(f"{base.rstrip('/')}/api/tags", timeout=5)
            server_up = r.status_code == 200
            if server_up:
                for m in r.json().get("models", []):
                    name = str(m.get("name", ""))
                    if _looks_like_embedding(name):
                        found = name
                        break
    except Exception:
        pass
    if not server_up:
        return {
            "ok": False, "provider": prov, "base_url": base, "model": "",
            "message": "No AI server reachable.",
            "howto": ("Start one first:\n"
                      "  LM Studio: start the local server (Developer tab)\n"
                      "  Ollama: ollama serve"),
        }
    if found:
        return {"ok": True, "provider": prov, "base_url": base,
                "model": found,
                "message": f"Embedding model available: {found}",
                "howto": ""}
    if prov == "lmstudio":
        howto = ("LM Studio: open the Models tab and search for:\n"
                 "  text-embedding-nomic-embed-text-v1.5\n"
                 "Download it (it loads automatically when used),\n"
                 "then press Build Vector DB again.")
    else:
        howto = ("Ollama: install an embedding model with:\n"
                 "  ollama pull nomic-embed-text\n"
                 "then press Build Vector DB again.")
    return {"ok": False, "provider": prov, "base_url": base, "model": "",
            "message": "No text-embedding model found on your AI server.",
            "howto": howto}


class EmbeddingStore:
    """Manage chunked textbook storage with vector embeddings.

    Auto-detects Ollama or LM Studio. Falls back to FTS5 if neither
    is running.
    """

    def __init__(self, base_url: str = "", provider: str = "auto"):
        self.db = get_db()
        self.provider, self.base_url = _detect_provider(provider, base_url)
        self._embedding_model = None  # lazy detected
        self._ensure_tables()

    def _detect_embedding_model(self) -> str:
        """Detect which model to use for embeddings."""
        if self._embedding_model:
            return self._embedding_model
        import requests
        try:
            if self.provider == "lmstudio":
                r = requests.get(f"{self.base_url}/v1/models", timeout=3)
                if r.status_code == 200:
                    models = r.json().get("data", [])
                    # Prefer a dedicated embedding model; never blindly take
                    # index 0 (usually an LLM, which cannot embed).
                    for m in models:
                        mid = str(m.get("id", ""))
                        if _looks_like_embedding(mid):
                            self._embedding_model = mid
                            return mid
                    self._embedding_model = "loaded"
                    return "loaded"
            else:
                r = requests.get(f"{self.base_url}/api/tags", timeout=3)
                if r.status_code == 200:
                    models = r.json().get("models", [])
                    for m in models:
                        name = m.get("name", "")
                        if "embed" in name.lower() or "nomic" in name.lower():
                            self._embedding_model = name
                            return name
                    # Fallback: use any available model
                    if models:
                        self._embedding_model = models[0].get("name", "llama3.2")
                        return self._embedding_model
        except Exception:
            pass
        # Defaults
        self._embedding_model = ("text-embedding-nomic-embed-text-v1.5"
                                 if self.provider == "lmstudio" else "nomic-embed-text")
        return self._embedding_model

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

    def _embed_source(self, name: str, content: str, batch_size: int,
                      throttle_ms: int, model: str, progress_cb=None,
                      _lock=None) -> list:
        """Chunk one book and embed every batch. No DB access (thread-safe).

        Returns [(chunk_index, chunk_text, blob_or_None), ...].
        """
        import time
        chunks = self._chunk_text(content)
        if progress_cb:
            with _lock:
                progress_cb(name, 0, len(chunks))
        out = []
        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start:batch_start + batch_size]
            embs = _get_embeddings_batch(
                batch, self.base_url, self.provider, model=model)
            for i, (chunk, emb) in enumerate(zip(batch, embs)):
                out.append((batch_start + i, chunk,
                            _pack_vector(emb) if emb else None))
            if batch_start + batch_size < len(chunks):
                time.sleep(throttle_ms / 1000.0)
            if progress_cb:
                with _lock:
                    progress_cb(name, min(batch_start + batch_size,
                                          len(chunks)), len(chunks))
        return out

    def build(self, batch_size: int = 10, throttle_ms: int = 500,
              progress_cb=None, jobs: int = 4) -> int:
        """Chunk all books, embed in batches, store in DB.

        Args:
            batch_size: texts per API call (default 10)
            throttle_ms: delay between batches (default 500ms)
            progress_cb: callback(source_name, chunks_done, total_chunks)
            jobs: books embedded in parallel (default 4). Workers never
                  touch the DB — one serial writer inserts everything.
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor
        count = self.db.execute("SELECT COUNT(*) FROM textbook_chunks WHERE embedding IS NOT NULL").fetchone()[0]
        if count > 0:
            print(f"Already have {count} chunks with embeddings — skipping")
            return count

        # Clean up any incomplete chunks (e.g., from failed runs)
        self.db.execute("DELETE FROM textbook_chunks")
        self.db.commit()

        model = self._detect_embedding_model()
        sources = [(r["source_name"], None) for r in self.db.execute(
            "SELECT source_name FROM knowledge_texts ORDER BY source_name"
        ).fetchall()]
        texts = {}
        for name, _ in sources:
            row = self.db.execute(
                "SELECT content FROM knowledge_texts WHERE source_name = ?", (name,)
            ).fetchone()
            if row:
                texts[name] = row["content"]

        lock = threading.Lock()

        def _work(name):
            return name, self._embed_source(
                name, texts[name], batch_size, throttle_ms, model,
                progress_cb=progress_cb, _lock=lock)

        total = 0
        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            for name, embedded in pool.map(_work, list(texts)):
                print(f"  {name}: {len(embedded)} chunks")
                for idx, chunk, blob in embedded:
                    self.db.execute(
                        "INSERT INTO textbook_chunks (source_name, chunk_index, content, embedding) "
                        "VALUES (?, ?, ?, ?)",
                        (name, idx, chunk, blob),
                    )
                    total += 1
                self.db.commit()
                self.db.execute("PRAGMA wal_checkpoint(PASSIVE)")

        self.db.commit()
        self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
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
                
            if end >= len(text):
                break
                
            start = end - CHUNK_OVERLAP
        return chunks

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Semantic search with cosine similarity, falling back to FTS5."""
        # Try embedding search first
        query_emb = _get_embedding(query, self.base_url, self.provider)
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
