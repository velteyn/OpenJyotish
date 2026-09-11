"""Tests for the AI Guru thread store (SQLite, isolated temp DB)."""

import pytest

from jhora.charts.chart import ChartBuilder


@pytest.fixture
def tmpdb(tmp_path):
    from jhora.core import database as db
    old_path = db._db_path
    db.set_db_path(str(tmp_path / "test-guru-history.db"))
    try:
        yield
    finally:
        db.close_all()
        db._db_path = old_path


@pytest.fixture(scope="module")
def chart():
    b = ChartBuilder()
    return b.build(year=2026, month=7, day=7, hour=10.5,
                   lat=13.08, lon=80.27, tz="+0530")


def _payload():
    return {
        "history": [{"role": "user", "content": "What is Shadbala?"},
                    {"role": "assistant", "content": "Sixfold strength."}],
        "transcript": [
            {"role": "user", "content": "What is Shadbala?"},
            {"role": "assistant", "content": "Sixfold strength.",
             "sources": [{"source": "BPHS", "excerpt": "strength..."}]},
        ],
    }


def test_round_trip_store_reload_delete(tmpdb, chart):
    from jhora.ai import guru_history as gh
    fp = gh.chart_fingerprint(chart)
    tid = gh.save_thread(fp, "Shadbala lesson", _payload())
    listed = gh.list_threads(fp)
    assert len(listed) == 1
    assert listed[0]["id"] == tid
    assert listed[0]["title"] == "Shadbala lesson"
    assert listed[0]["updated_at"]
    assert listed[0]["messages"] == 2
    loaded = gh.load_thread(tid)
    assert loaded["history"] == _payload()["history"]
    assert loaded["transcript"][1]["sources"] == [
        {"source": "BPHS", "excerpt": "strength..."}]
    gh.delete_thread(tid)
    assert gh.list_threads(fp) == []
    assert gh.load_thread(tid) == {"history": [], "transcript": []}


def test_resume_updates_same_row(tmpdb, chart):
    from jhora.ai import guru_history as gh
    fp = gh.chart_fingerprint(chart)
    tid = gh.save_thread(fp, "Shadbala lesson", _payload())
    grown = {"history": _payload()["history"] + [
        {"role": "user", "content": "And Hora?"}],
        "transcript": _payload()["transcript"]}
    assert gh.save_thread(fp, "Shadbala lesson", grown, thread_id=tid) == tid
    assert len(gh.list_threads(fp)) == 1
    assert len(gh.load_thread(tid)["history"]) == 3


def test_prune_keeps_newest_fifty(tmpdb, chart):
    from jhora.ai import guru_history as gh
    fp = gh.chart_fingerprint(chart)
    for i in range(55):
        gh.save_thread(fp, f"lesson {i:02d}", _payload())
    listed = gh.list_threads(fp)
    assert len(listed) == 50
    titles = [t["title"] for t in listed]
    assert "lesson 54" in titles
    for i in range(5):
        assert f"lesson {i:02d}" not in titles


def test_chartless_study_has_own_scope(tmpdb, chart):
    from jhora.ai import guru_history as gh
    assert gh.chart_fingerprint(None) == gh.GENERAL_SCOPE
    tid = gh.save_thread(gh.GENERAL_SCOPE, "General study", _payload())
    assert len(gh.list_threads(gh.GENERAL_SCOPE)) == 1
    assert len(gh.list_threads(gh.chart_fingerprint(chart))) == 0
    gh.delete_thread(tid)


def test_fingerprint_stable_and_chart_specific(tmpdb, chart):
    from jhora.ai import guru_history as gh
    assert gh.chart_fingerprint(chart) == gh.chart_fingerprint(chart)
    b = ChartBuilder()
    other = b.build(year=1973, month=3, day=13, hour=13.9,
                    lat=45.41, lon=11.88, tz="+0100")
    assert gh.chart_fingerprint(other) != gh.chart_fingerprint(chart)


def test_thread_title_from_first_message():
    from jhora.ai import guru_history as gh
    assert gh.thread_title(_payload()["history"]) == "What is Shadbala?"
    assert gh.thread_title([]) == "Untitled lesson"
