"""Public-domain seed library: provenance record stays consistent."""

import re
from pathlib import Path

BOOKS = Path(__file__).resolve().parents[1] / "src" / "jhora" / "data" / "books"


def _sources_text():
    return (BOOKS / "SOURCES-PD.md").read_text(encoding="utf-8")


def test_books_dir_resolves_with_texts():
    from jhora.paths import pd_books_dir
    d = pd_books_dir()
    assert d is not None and d.is_dir()
    assert len(list(d.glob("*.txt"))) >= 3


def test_every_text_has_provenance():
    text = _sources_text().lower()
    for f in BOOKS.glob("*.txt"):
        stem = f.stem.lower()
        assert stem.split("-")[0] in text, f.name
    n_files = len(list(BOOKS.glob("*.txt")))
    evidenced = text.count("rights evidence") + text.count("original synthesis")
    assert evidenced >= n_files


def test_every_entry_states_distinct_value():
    text = _sources_text()
    entries = re.findall(r"^## \d+\. .*?$", text, re.MULTILINE)
    assert len(entries) == len(list(BOOKS.glob("*.txt")))
    for entry in entries:
        section = text.split(entry, 1)[1].split("## ", 1)[0]
        assert "Distinct value:" in section, entry


def test_no_modern_editions():
    text = _sources_text().split("deliberately NOT here")[0]
    for bad in ["Santhanam", "Raman", "Rao", "Rath", "1997", "2000"]:
        assert bad not in text, bad


def test_pd_text_loads_and_searches(tmp_path):
    import shutil
    from jhora.interpreter.knowledge_base import KnowledgeBase
    from jhora.core.database import get_db
    src = next(BOOKS.glob("*.txt"))
    probe = tmp_path / "pd-probe.txt"
    shutil.copy(src, probe)
    name = None
    try:
        kb = KnowledgeBase(books_dir=tmp_path)
        assert kb.loaded >= 1
        hits = kb.search("Jupiter houses planets signs")
        assert hits, "PD text not searchable"
        name = hits[0]["source"]
    finally:
        db = get_db()
        db.execute("DELETE FROM knowledge_texts WHERE source_name LIKE 'Pd Probe%'")
        db.execute("DELETE FROM knowledge_texts WHERE source_name = ?", (name or "",))
        db.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
        db.commit()


def test_dash_name_normalized(tmp_path):
    from jhora.interpreter.knowledge_base import KnowledgeBase
    from jhora.core.database import get_db
    f = tmp_path / "my-test-book.txt"
    f.write_text("Jupiter is benefic. Saturn is malefic. " * 30)
    try:
        KnowledgeBase(books_dir=tmp_path)
        row = get_db().execute(
            "SELECT source_name FROM knowledge_texts "
            "WHERE source_name = 'My Test Book'").fetchone()
        assert row is not None
    finally:
        db = get_db()
        db.execute("DELETE FROM knowledge_texts WHERE source_name = 'My Test Book'")
        db.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
        db.commit()
