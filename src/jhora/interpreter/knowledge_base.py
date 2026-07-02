"""Knowledge base: load, index and search the extracted book+articles."""

import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BOOKS_DIR = Path(__file__).resolve().parents[3] / "docs" / "books" / "extracted"


class KnowledgeBase:
    """Full-text search over extracted PDF text."""

    def __init__(self, books_dir: Optional[Path] = None):
        self.books_dir = books_dir or BOOKS_DIR
        self.docs: Dict[str, str] = {}
        self._load()

    def _load(self):
        if not self.books_dir.exists():
            return
        for f in sorted(self.books_dir.glob("*.txt")):
            name = f.stem.replace("_", " ").replace(".pdf", "").title()
            with open(f, encoding="utf-8") as fh:
                self.docs[name] = fh.read()

    @property
    def loaded(self) -> int:
        return len(self.docs)

    def list_sources(self) -> List[str]:
        return list(self.docs.keys())

    def search(self, query: str, max_results: int = 5, context_chars: int = 300) -> List[dict]:
        """Search across all documents, return ranked excerpts."""
        q = _normalize(query)
        results = []

        for title, text in self.docs.items():
            text_norm = _normalize(text)
            pos = 0
            while True:
                idx = text_norm.find(q, pos)
                if idx == -1 or len(results) >= max_results * 3:
                    break
                start = max(0, idx - context_chars // 2)
                end = min(len(text), idx + len(q) + context_chars // 2)
                excerpt = text[start:end].strip()
                excerpt = excerpt[:500]
                score = _score_match(text, idx)
                results.append({
                    "source": title,
                    "excerpt": excerpt,
                    "score": score,
                    "context_start": start,
                    "context_end": end,
                })
                pos = idx + 1

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:max_results]

    def get_source(self, title: str) -> Optional[str]:
        return self.docs.get(title)

    def topics(self) -> List[str]:
        topics = set()
        keywords = [
            "dasa", "varga", "yoga", "graha", "rasi", "bhava", "lagna",
            "shadbala", "ashtakavarga", "tajaka", "transit", "remedy",
            "muhurta", "matchmaking", "prasna", "nakshatra", "karaka",
        ]
        for title in self.docs:
            for kw in keywords:
                if kw in title.lower():
                    topics.add(kw)
        return sorted(topics)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _score_match(text: str, idx: int) -> float:
    """Score a match by position in document (earlier = higher)."""
    return 1.0 / (1.0 + idx / 1000.0)
