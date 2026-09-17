"""Tests for parallel vector-DB build + embedding-model pre-flight."""

import sys

import pytest

import jhora.ai.embeddings as emb
from jhora.ai.embeddings import EmbeddingStore, embedding_model_status


def _fake_catalog(monkeypatch, lmstudio_models=None, ollama_models=None,
                  refuse=False):
    import requests

    def fake_get(url, timeout=5):
        if refuse:
            raise requests.exceptions.ConnectionError("refused")
        if "/v1/models" in url:
            return _Resp({"data": lmstudio_models or []})
        if "/api/tags" in url:
            return _Resp({"models": ollama_models or []})
        raise AssertionError(url)
    monkeypatch.setattr(requests, "get", fake_get)


class _Resp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


class TestPreflight:
    def test_lmstudio_embed_found(self, monkeypatch):
        _fake_catalog(monkeypatch, lmstudio_models=[
            {"id": "some-llm"}, {"id": "text-embedding-nomic-embed-text-v1.5"}])
        r = embedding_model_status(base_url="http://x:1234",
                                   provider="lmstudio")
        assert r["ok"] is True
        assert r["model"] == "text-embedding-nomic-embed-text-v1.5"

    def test_lmstudio_embed_missing_advises_download(self, monkeypatch):
        _fake_catalog(monkeypatch,
                      lmstudio_models=[{"id": "some-llm"}])
        r = embedding_model_status(base_url="http://x:1234",
                                   provider="lmstudio")
        assert r["ok"] is False
        assert "nomic-embed" in r["howto"]
        assert "Models tab" in r["howto"]

    def test_ollama_embed_missing_advises_pull(self, monkeypatch):
        _fake_catalog(monkeypatch, ollama_models=[{"name": "qwen3:8b"}])
        r = embedding_model_status(base_url="http://x:11434",
                                   provider="ollama")
        assert r["ok"] is False
        assert "ollama pull nomic-embed-text" in r["howto"]

    def test_server_down_says_start(self, monkeypatch):
        _fake_catalog(monkeypatch, refuse=True)
        r = embedding_model_status(base_url="http://x:1234",
                                   provider="lmstudio")
        assert r["ok"] is False
        assert "Start one" in r["howto"]


class TestParallelBuild:
    @staticmethod
    def _dump(db):
        return db.execute(
            "SELECT source_name, chunk_index, content, embedding "
            "FROM textbook_chunks ORDER BY source_name, chunk_index"
        ).fetchall()

    def test_parallel_matches_serial(self, monkeypatch):
        import jhora.ai.embeddings as e

        def fake_batch(texts, base_url, provider, model=""):
            return [[float(len(t))] * 8 for t in texts]
        monkeypatch.setattr(e, "_get_embeddings_batch", fake_batch)
        monkeypatch.setattr(e.EmbeddingStore, "_detect_embedding_model",
                            lambda self: "fake")

        store = EmbeddingStore(provider="lmstudio",
                               base_url="http://x:1234")
        db = store.db
        saved = [tuple(r) for r in self._dump(db)]
        try:
            # start empty so both builds really run (restored in finally)
            db.execute("DELETE FROM textbook_chunks")
            db.commit()
            serial = store.build(batch_size=50, throttle_ms=0, jobs=1)
            rows_serial = {(r[0], r[1], r[2]) for r in self._dump(db)}
            db.execute("DELETE FROM textbook_chunks")
            db.commit()
            parallel = store.build(batch_size=50, throttle_ms=0, jobs=4)
            rows_parallel = {(r[0], r[1], r[2]) for r in self._dump(db)}
            assert serial == parallel > 0
            assert rows_serial == rows_parallel
            # embeddings actually stored
            n = db.execute("SELECT COUNT(*) FROM textbook_chunks "
                           "WHERE embedding IS NOT NULL").fetchone()[0]
            assert n == parallel
        finally:
            db.execute("DELETE FROM textbook_chunks")
            for r in saved:
                db.execute(
                    "INSERT INTO textbook_chunks "
                    "(source_name, chunk_index, content, embedding) "
                    "VALUES (?, ?, ?, ?)", r)
            db.commit()


@pytest.fixture(scope="module")
def _qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_build_button_blocked_without_embed_model(_qapp, monkeypatch):
    import jhora.ai.embeddings as emb
    from jhora.ui.main_window import MainWindow
    monkeypatch.setattr(emb, "embedding_model_status",
                        lambda provider="auto": {
                            "ok": False, "message": "No model",
                            "howto": "Download X"})
    shown = {}
    monkeypatch.setattr("jhora.ui.main_window.QMessageBox.warning",
                        lambda *a, **k: shown.setdefault("msg", a[2]))
    window = MainWindow()
    window._on_ai_vdb_build()
    assert "Download X" in shown.get("msg", "")
    assert not hasattr(window, "_vdb_worker")
    assert window.ai_vdb_build.isEnabled()


def test_vector_search_skips_dim_mismatch():
    """A query vector from another embedding model must not crash search."""
    from jhora.ai.embeddings import EmbeddingStore
    store = EmbeddingStore(provider="lmstudio", base_url="http://x:1234")
    res = store._vector_search([0.1] * 384, top_k=3)
    assert res == []


class TestFreshInstallSeeding:
    """Fresh downloads ship an empty knowledge_texts table — the vector
    build must seed it from the bundled library (our Primer + PD classics)
    instead of storing 0 chunks, and Learn must still cite books."""

    @staticmethod
    def _tmp_db(tmp_path, name):
        from jhora.core import database as db
        old = db._db_path
        db.set_db_path(str(tmp_path / name))
        return old

    @staticmethod
    def _restore(old):
        from jhora.core import database as db
        db.close_all()
        db._db_path = old

    def test_build_seeds_shipped_texts(self, tmp_path, monkeypatch):
        import jhora.ai.embeddings as e
        old = self._tmp_db(tmp_path, "fresh.db")
        try:
            monkeypatch.setattr(
                e, "_get_embeddings_batch",
                lambda texts, base_url, provider, model="":
                    [[0.1] * 8 for _ in texts])
            monkeypatch.setattr(e.EmbeddingStore, "_detect_embedding_model",
                                lambda self: "fake")
            store = e.EmbeddingStore(provider="lmstudio",
                                     base_url="http://x:1234")
            assert store.db.execute(
                "SELECT COUNT(*) FROM knowledge_texts").fetchone()[0] == 0
            n = store.build(batch_size=50, throttle_ms=0, jobs=1)
            assert n > 0
            names = {r[0] for r in store.db.execute(
                "SELECT source_name FROM knowledge_texts").fetchall()}
            assert "Primer 01 Foundations" in names
        finally:
            self._restore(old)

    def test_search_falls_back_to_fts_when_chunks_empty(
            self, tmp_path, monkeypatch):
        import jhora.ai.embeddings as e
        old = self._tmp_db(tmp_path, "fresh2.db")
        try:
            from jhora.interpreter.knowledge_base import KnowledgeBase
            KnowledgeBase()  # seed texts, but no vector build
            monkeypatch.setattr(e, "_get_embedding",
                                lambda q, base, prov: [0.1] * 8)
            store = e.EmbeddingStore(provider="lmstudio",
                                     base_url="http://x:1234")
            res = store.search("Jupiter dasha effects", top_k=3)
            assert res, "Learn gets no textbook backing without a vector build"
        finally:
            self._restore(old)


def test_ai_base_url_follows_provider(_qapp):
    from jhora.ui.main_window import MainWindow
    window = MainWindow()
    window.ai_provider.setCurrentText("unsloth")
    assert "8000" in window.ai_base_url.text()
    window.ai_base_url.setText("http://192.0.2.10:8888/v1")
    engine = window._get_ai_engine()
    assert engine.config.base_url == "http://192.0.2.10:8888/v1"


def test_ai_status_readable(_qapp):
    """Status errors must be visible: wrapped, multi-line, selectable."""
    from PyQt6.QtCore import Qt
    from jhora.ui.main_window import MainWindow
    window = MainWindow()
    assert window.ai_status.wordWrap() is True
    assert window.ai_status.minimumHeight() >= 40
    assert bool(window.ai_status.textInteractionFlags()
                & Qt.TextInteractionFlag.TextSelectableByMouse)


def test_check_populates_model_combo(_qapp, monkeypatch):
    import jhora.ui.main_window as mw
    from jhora.ui.main_window import MainWindow

    class _FakeEngine:
        def __init__(self, *a, **k):
            pass

        def health_check(self):
            return {"ok": True, "models": ["a", "b"],
                    "status": "ok", "model": "b",
                    "message": "Using b", "available": ["a", "b"]}

        def catalog_detail(self):
            return [{"id": "a", "display": "a", "loaded": False,
                     "ctx": 0},
                    {"id": "b", "display": "b", "loaded": True,
                     "ctx": 8448}]

    monkeypatch.setattr(mw, "AiEngine", _FakeEngine)
    window = MainWindow()
    window._on_ai_health_check()
    items = [window.ai_model.itemText(i)
             for i in range(window.ai_model.count())]
    assert items[0] == "loaded"
    assert "a" in items and "b" in items
    assert "8448" in window.ai_status.text()
    assert "b" in window.ai_status.text()
