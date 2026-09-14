"""Personal library import: user .txt books land in the DB (cleaned up)."""

import sys

import pytest


@pytest.fixture()
def _user_books(tmp_path, monkeypatch):
    import jhora.paths as paths
    monkeypatch.setattr(paths, "user_books_dir", lambda: tmp_path / "books")
    return tmp_path / "books"


def _cleanup(names):
    from jhora.core.database import get_db
    db = get_db()
    for n in names:
        db.execute("DELETE FROM knowledge_texts WHERE source_name = ?", (n,))
    db.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
    db.commit()


def test_import_txt_books(_user_books, tmp_path):
    from jhora.interpreter.knowledge_base import KnowledgeBase
    f1 = tmp_path / "Test Tome Alpha.txt"
    f2 = tmp_path / "Test Tome Beta.txt"
    f1.write_text("Jupiter signifies wisdom and expansion in every chart. " * 20)
    f2.write_text("Saturn signifies discipline and karmic debts always. " * 20)
    try:
        res = KnowledgeBase().import_files([str(f1), str(f2), str(f1)])
        assert sorted(res["added"]) == ["Test Tome Alpha", "Test Tome Beta"]
        assert any("already imported" in s for s in res["skipped"])
        kb = KnowledgeBase()
        hits = kb.search("Jupiter wisdom expansion")
        assert any(h["source"] == "Test Tome Alpha" for h in hits)
    finally:
        _cleanup(["Test Tome Alpha", "Test Tome Beta"])


def test_import_rejects_non_txt(_user_books, tmp_path):
    from jhora.interpreter.knowledge_base import KnowledgeBase
    f = tmp_path / "evil.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    res = KnowledgeBase().import_files([str(f)])
    assert res["added"] == []
    assert any("not a .txt" in s for s in res["skipped"])


def test_cli_knowledge_import(_user_books, tmp_path):
    from typer.testing import CliRunner
    from jhora.cli.main import app
    f = tmp_path / "Cli Tome Gamma.txt"
    f.write_text("Venus signifies love and harmony in all houses. " * 20)
    try:
        r = CliRunner().invoke(app, ["knowledge-import", str(f)])
        assert r.exit_code == 0, r.output
        assert "Cli Tome Gamma" in r.output
    finally:
        _cleanup(["Cli Tome Gamma"])


@pytest.fixture(scope="module")
def _qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_import_button_exists(_qapp):
    from jhora.ui.main_window import MainWindow
    window = MainWindow()
    assert window.kb_import_btn.text() == "Import books…"
