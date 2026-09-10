"""Tests for the AI Chat thread store (SQLite, isolated temp DB)."""

import pytest

from jhora.charts.chart import ChartBuilder


@pytest.fixture
def tmpdb(tmp_path):
    from jhora.core import database as db
    old_path = db._db_path
    db.set_db_path(str(tmp_path / "test-history.db"))
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


def _messages(n=1):
    return ([{"role": "user", "content": "What about my career?"},
             {"role": "assistant", "content": "Mars in the 10th house."}] * n)


def _payload(n=1):
    return {"history": _messages(n),
            "transcript": _messages(n) + [{"role": "divider",
                                           "content": "compacted"}]}


def test_round_trip_store_reload_delete(tmpdb, chart):
    from jhora.ai import chat_history as ch
    fp = ch.chart_fingerprint(chart)
    tid = ch.save_thread(fp, "Career question", _payload())
    listed = ch.list_threads(fp)
    assert len(listed) == 1
    assert listed[0]["id"] == tid
    assert listed[0]["title"] == "Career question"
    assert listed[0]["updated_at"]
    assert listed[0]["messages"] == 2
    assert ch.load_thread(tid) == _payload()
    ch.delete_thread(tid)
    assert ch.list_threads(fp) == []
    assert ch.load_thread(tid) == {"history": [], "transcript": []}


def test_resume_updates_same_row(tmpdb, chart):
    from jhora.ai import chat_history as ch
    fp = ch.chart_fingerprint(chart)
    tid = ch.save_thread(fp, "Career question", _payload())
    grown_hist = _messages() + [{"role": "user", "content": "And marriage?"},
                                {"role": "assistant", "content": "Venus strong."}]
    grown = {"history": grown_hist, "transcript": grown_hist}
    assert ch.save_thread(fp, "Career question", grown, thread_id=tid) == tid
    assert len(ch.list_threads(fp)) == 1
    assert ch.load_thread(tid) == grown


def test_prune_keeps_newest_fifty(tmpdb, chart):
    from jhora.ai import chat_history as ch
    fp = ch.chart_fingerprint(chart)
    for i in range(55):
        ch.save_thread(fp, f"thread {i:02d}", _messages())
    listed = ch.list_threads(fp)
    assert len(listed) == 50
    titles = [t["title"] for t in listed]
    assert "thread 54" in titles  # newest kept
    for i in range(5):
        assert f"thread {i:02d}" not in titles  # oldest pruned


def test_prune_is_per_chart(tmpdb, chart):
    from jhora.ai import chat_history as ch
    other_fp = "2026-01-01 00:00|0.0000|0.0000|+0000"
    for i in range(55):
        ch.save_thread(ch.chart_fingerprint(chart), f"t{i:02d}", _messages())
    ch.save_thread(other_fp, "other chart thread", _messages())
    assert len(ch.list_threads(ch.chart_fingerprint(chart))) == 50
    assert len(ch.list_threads(other_fp)) == 1


def test_fingerprint_stable_and_chart_specific(tmpdb, chart):
    from jhora.ai import chat_history as ch
    assert ch.chart_fingerprint(chart) == ch.chart_fingerprint(chart)
    b = ChartBuilder()
    other = b.build(year=1973, month=3, day=13, hour=13.9,
                    lat=45.41, lon=11.88, tz="+0100")
    assert ch.chart_fingerprint(other) != ch.chart_fingerprint(chart)


def test_thread_title_from_first_message():
    from jhora.ai import chat_history as ch
    assert ch.thread_title(_messages()) == "What about my career?"
    long_q = [{"role": "user", "content": "x" * 100}]
    assert ch.thread_title(long_q) == "x" * 40 + "..."
    assert ch.thread_title([]) == "Untitled thread"
    assert ch.thread_title([{"role": "user", "content": "  "}]) == "Untitled thread"
