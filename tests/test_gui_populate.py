"""GUI populate tests — exercises every MainWindow populate method.

Uses QApplication with offscreen platform so it runs without a display.
Catches ALL attribute errors, unpacking errors, NameErrors etc. in one run.
"""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import datetime
import pytest
from PyQt6.QtWidgets import QApplication

from jhora.ui.main_window import MainWindow
from jhora.charts.chart import ChartBuilder


@pytest.fixture(scope="module")
def _qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="module")
def main_window(_qapp):
    return MainWindow()


@pytest.fixture(scope="module")
def chart():
    b = ChartBuilder()
    return b.build(1973, 3, 13, 13.0 + 55 / 60.0, 45.41, 11.88, tz="+0100")


# ── Each test calls one MainWindow populate method ──

def test_populate_consolidated(main_window, chart):
    main_window.chart_data = chart
    main_window._populate_consolidated(chart)


def test_populate_cons_planet_table(main_window, chart):
    main_window._populate_cons_planet_table(chart)


def test_populate_cons_natal_panel(main_window, chart):
    main_window._populate_cons_natal_panel(chart)


def test_populate_cons_ashtakavarga(main_window, chart):
    main_window._populate_cons_ashtakavarga(chart)


def test_populate_dashboard(main_window, chart):
    main_window._populate_dashboard(chart)


def test_populate_arudha_table(main_window, chart):
    main_window._populate_arudha_table(chart)


def test_populate_shadbala_table(main_window, chart):
    main_window._populate_shadbala_table(chart)


def test_populate_ashtakavarga_table(main_window, chart):
    main_window._populate_ashtakavarga_table(chart)


def test_populate_transit_table(main_window, chart):
    main_window._populate_transit_table(chart)


def test_populate_tithi_pravesha(main_window, chart):
    main_window._populate_tithi_pravesha(chart)


def test_populate_progressions(main_window, chart):
    main_window._populate_progressions(chart)


def test_dasa_timeline(main_window, chart):
    main_window.dasa_timeline.set_chart(chart)


# ── AI Settings tab tests ──

def test_ai_settings_widgets(main_window):
    """AI Chat tab has provider config."""
    assert hasattr(main_window, 'ai_provider')
    assert hasattr(main_window, 'ai_model')
    assert hasattr(main_window, 'ai_check_btn')


def test_ai_chat_buttons_created(main_window):
    """AI Chat action buttons exist."""
    assert hasattr(main_window, 'ai_interpret_btn')
    assert hasattr(main_window, 'ai_remedy_btn')
    assert hasattr(main_window, 'ai_ask_btn')


def test_ai_settings_provider_defaults(main_window):
    """Provider defaults to ollama (since restored to original)."""
    assert main_window.ai_provider.currentText() == "ollama"


def test_ai_settings_provider_change(main_window):
    """Changing provider updates model."""
    main_window.ai_provider.setCurrentText("ollama")
    assert main_window.ai_model.text() != ""


def test_ai_chat_status_exists(main_window):
    """Provider widgets exist in AI Chat tab."""
    assert hasattr(main_window, 'ai_provider')
    assert hasattr(main_window, 'ai_status')


def test_old_provider_widgets_removed(main_window):
    """Old Settings tab provider widgets don't exist (restored to Chat tab)."""
    assert not hasattr(main_window, 'ai_settings_provider')


# ── Dasa tab option widgets ──

def test_dasa_option_widgets_exist(main_window):
    """Dasa tab has seed/sesham/year controls."""
    assert hasattr(main_window, 'dasa_seed_combo')
    assert hasattr(main_window, 'dasa_sesham_combo')
    assert hasattr(main_window, 'dasa_year_combo')


def test_dasa_seed_defaults_to_moon(main_window):
    assert main_window.dasa_seed_combo.currentText() == "Moon"


def test_dasa_sesham_defaults_to_moon(main_window):
    assert main_window.dasa_sesham_combo.currentText().startswith("Moon")


def test_dasa_year_defaults_to_solar(main_window):
    assert main_window.dasa_year_combo.currentText() == "Solar"


def test_dasa_options_build(main_window):
    """_dasa_options maps dropdown text to DasaOptions correctly."""
    opts = main_window._dasa_options()
    assert opts.start_variation == "moon"
    assert opts.sesham_method == "moon"
    assert opts.year_definition == "solar"


def test_dasa_options_respect_selection(main_window):
    main_window.dasa_seed_combo.setCurrentText("Lagna")
    main_window.dasa_sesham_combo.setCurrentText("Full (120yr cycle)")
    main_window.dasa_year_combo.setCurrentText("Tithi")
    opts = main_window._dasa_options()
    assert opts.start_variation == "lagna"
    assert opts.sesham_method == "full"
    assert opts.year_definition == "tithi"


def test_update_dasa_text_with_options(main_window, chart):
    """Full dasa text render with custom seed does not crash."""
    main_window.chart_data = chart
    main_window.dasa_seed_combo.setCurrentText("Sun")
    main_window._update_dasa_text()
    assert main_window.dasa_text.toPlainText() != ""


# ── User's Special Lagna (USL) widgets ──

def test_usl_widgets_exist(main_window):
    assert hasattr(main_window, 'usl_planet_combo')
    assert hasattr(main_window, 'usl_factor_spin')
    assert hasattr(main_window, 'usl_reverse_cb')
    assert hasattr(main_window, 'usl_apply_btn')


def test_usl_planet_default_jupiter(main_window):
    assert main_window.usl_planet_combo.currentText() == "Ju"


def test_usl_apply_populates_table(main_window, chart):
    main_window.chart_data = chart
    main_window.usl_planet_combo.setCurrentText("Ju")
    main_window.usl_factor_spin.setValue(9.0)
    main_window._apply_usl()
    assert main_window._usl_lon is not None
    assert main_window._usl_config is not None
    from jhora.calc.special_lagnas import user_special_lagna_name
    assert user_special_lagna_name(main_window._usl_config) == "Ju9"
    # The USL row should be visible in the table
    found = False
    for row in range(main_window.cons_planet_table.rowCount()):
        item = main_window.cons_planet_table.item(row, 0)
        if item and item.text() == "Ju9":
            found = True
            break
    assert found


def test_cons_table_has_classic_special_lagnas(main_window, chart):
    main_window.chart_data = chart
    main_window._populate_cons_planet_table(chart)
    cols = [main_window.cons_planet_table.item(r, 0).text()
            for r in range(main_window.cons_planet_table.rowCount())
            if main_window.cons_planet_table.item(r, 0)]
    for name in ["Bhrigu Bindu", "Indu Lagna", "Varnada Lagna",
                 "Pranapada Lagna", "Vighati Lagna", "Upapada Lagna",
                 "Bhava Lagna", "Hora Lagna", "Ghati Lagna", "Sree Lagna"]:
        assert name in cols, f"missing {name} in consolidated table"


def test_thinking_indicator_shows_then_clears_on_answer(main_window):
    """The 'Thinking…' affordance appears during the hidden reasoning phase and
    is replaced once the model streams an answer."""
    main_window._ai_transcript = [{"role": "user", "content": "q"}]
    main_window._ai_stream = ""
    main_window._ai_thinking = True
    main_window._render_ai_output()
    html = main_window.ai_output.toHtml()
    assert "Thinking" in html or "⏳" in html

    main_window._on_ai_token("The Moon in Aries ")
    assert main_window._ai_thinking is False
    main_window._render_ai_output()
    html = main_window.ai_output.toHtml()
    assert "The Moon in Aries" in html
    main_window._ai_transcript = []
    main_window._ai_stream = ""


def test_thinking_indicator_clears_on_done(main_window):
    main_window._ai_transcript = [{"role": "user", "content": "q"}]
    main_window._ai_stream = "partial answer"
    main_window._ai_thinking = True
    main_window._ai_worker = None
    main_window._on_ai_done()
    assert main_window._ai_thinking is False
    main_window._ai_transcript = []
    main_window._ai_stream = ""


def test_ai_transcript_appends_two_turns(main_window):
    """Two completed ask turns render oldest-first from the transcript list,
    and the canonical worker history wins over streamed tail text."""

    class _FakeAskWorker:
        mode = "ask"
        result_reset = False
        result_history = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "Canonical A1"},
        ]

    main_window._ai_transcript = []
    main_window._ai_history = []
    main_window._ai_stream = ""
    main_window._ai_thinking = False
    previous_chart = main_window.chart_data
    main_window.chart_data = None  # no persist: done-hook needs a chart
    # First turn completes with streamed text differing from canonical.
    main_window._ai_transcript.append({"role": "user", "content": "Q1"})
    main_window._ai_stream = "drifted tail"
    main_window._ai_worker = _FakeAskWorker()
    main_window._on_ai_done()
    assert main_window._ai_history == _FakeAskWorker.result_history
    # Second turn appends below the first.
    main_window._ai_transcript.append({"role": "user", "content": "Q2"})
    main_window._ai_transcript.append({"role": "assistant", "content": "A2"})
    main_window._render_ai_output()
    html = main_window.ai_output.toHtml()
    positions = [html.find(s) for s in ("Q1", "Canonical A1", "Q2", "A2")]
    assert all(p >= 0 for p in positions), "all four blocks visible"
    assert positions == sorted(positions), "oldest-first order"
    assert "drifted tail" not in html, "canonical history wins"
    main_window.chart_data = previous_chart
    main_window._ai_transcript = []
    main_window._ai_history = []
    main_window._ai_worker = None


def test_ai_interpret_appends_after_ask_exchange(main_window):
    """An Interpret result becomes a transcript entry below the prior Ask
    exchange, recorded into the thread history with its exact worker text."""

    class _FakeInterpretWorker:
        mode = "interpret"
        result_text = "Full interpretation text."

    main_window._ai_transcript = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
    ]
    main_window._ai_history = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
    ]
    previous_chart = main_window.chart_data
    main_window.chart_data = None  # no persist: done-hook needs a chart
    main_window._ai_pending_user = "[Interpret — detailed · general]"
    main_window._ai_transcript.append(
        {"role": "user", "content": main_window._ai_pending_user})
    main_window._ai_stream = "partial stream..."
    main_window._ai_thinking = True
    main_window._ai_worker = _FakeInterpretWorker()
    main_window._on_ai_done()
    main_window._render_ai_output()
    html = main_window.ai_output.toHtml()
    positions = [html.find(s) for s in
                 ("Q1", "A1", "Interpret", "Full interpretation text.")]
    assert all(p >= 0 for p in positions), "ask + interpret entries visible"
    assert positions == sorted(positions), "ask exchange stays above interpret"
    assert "partial stream" not in html, "exact worker text wins"
    assert main_window._ai_history[-2:] == [
        {"role": "user", "content": "[Interpret — detailed · general]"},
        {"role": "assistant", "content": "Full interpretation text."},
    ], "thread history records the exchange"
    main_window.chart_data = previous_chart
    main_window._ai_transcript = []
    main_window._ai_history = []
    main_window._ai_worker = None


def test_ai_compaction_renders_divider_keeps_history(main_window, chart,
                                                     tmp_path):
    """An over-budget turn inserts a divider above the fresh exchange while
    prior exchanges stay visible, and the meter shows live numbers."""
    from jhora.core import database as db
    old_db_path = db._db_path
    db.set_db_path(str(tmp_path / "gui-divider.db"))

    class _FakeResetWorker:
        mode = "ask"
        result_reset = True
        result_history = [
            {"role": "user", "content": "new Q"},
            {"role": "assistant", "content": "fresh A"},
        ]

    previous_chart = main_window.chart_data
    main_window.chart_data = chart
    main_window._ai_transcript = [
        {"role": "user", "content": "old Q"},
        {"role": "assistant", "content": "old A"},
        {"role": "user", "content": "new Q"},
    ]
    main_window._ai_history = [
        {"role": "user", "content": "old Q"},
        {"role": "assistant", "content": "old A"},
    ]
    main_window._ai_stream = ""
    main_window._ai_thinking = True
    main_window._ai_worker = _FakeResetWorker()
    try:
        main_window._on_ai_done()
        roles = [b["role"] for b in main_window._ai_transcript]
        assert roles == ["user", "assistant", "divider", "user", "assistant"]
        assert main_window._ai_history == _FakeResetWorker.result_history
        main_window._render_ai_output()
        html = main_window.ai_output.toHtml()
        positions = [html.find(s) for s in
                     ("old Q", "old A", "compacted", "new Q", "fresh A")]
        assert all(p >= 0 for p in positions), "history + divider visible"
        assert positions == sorted(positions), "divider sits above new turn"
        meter = main_window.ai_context_label.text()
        assert meter.startswith("Context: "), meter
        assert "%" in meter
    finally:
        main_window.chart_data = previous_chart
        main_window._ai_transcript = []
        main_window._ai_history = []
        main_window._ai_worker = None
        main_window._ai_thread_id = None
        main_window._ai_thread_title = ""
        db.close_all()
        db._db_path = old_db_path


def _isolate_ai_db(tmp_path, name):
    from jhora.core import database as db
    old = db._db_path
    db.set_db_path(str(tmp_path / name))
    return old


def _restore_ai_db(old):
    from jhora.core import database as db
    db.close_all()
    db._db_path = old


def test_ai_newchat_shelves_resume_restores_delete(main_window, chart,
                                                   tmp_path):
    """Full thread lifecycle: shelve on New chat, resume via picker, delete
    clears; second turns update the same row."""
    old_db = _isolate_ai_db(tmp_path, "gui-lifecycle.db")
    previous_chart = main_window.chart_data
    main_window.chart_data = chart
    try:
        # One completed exchange, unshelved: persist assigns an id.
        main_window._ai_history = [
            {"role": "user", "content": "Career?"},
            {"role": "assistant", "content": "Mars tenth."},
        ]
        main_window._ai_transcript = [
            {"role": "user", "content": "Career?"},
            {"role": "assistant", "content": "Mars tenth."},
        ]
        main_window._ai_thread_id = None
        main_window._persist_ai_thread()
        tid = main_window._ai_thread_id
        assert tid is not None
        assert main_window.ai_thread_combo.count() == 1
        # A second turn updates the same row, not a new one.
        main_window._ai_history += [
            {"role": "user", "content": "Marriage?"},
            {"role": "assistant", "content": "Venus strong."},
        ]
        main_window._ai_transcript += [
            {"role": "user", "content": "Marriage?"},
            {"role": "assistant", "content": "Venus strong."},
        ]
        main_window._persist_ai_thread()
        assert main_window._ai_thread_id == tid
        assert main_window.ai_thread_combo.count() == 1
        # New chat clears the view but the shelved thread remains.
        main_window._on_ai_newchat()
        assert main_window._ai_transcript == []
        assert main_window._ai_history == []
        assert main_window._ai_thread_id is None
        assert main_window.ai_thread_combo.count() == 1
        assert main_window.ai_thread_combo.currentIndex() == -1
        # Resume through the real signal path restores everything.
        main_window.ai_thread_combo.setCurrentIndex(0)
        assert main_window._ai_thread_id == tid
        assert len(main_window._ai_history) == 4
        assert [b["role"] for b in main_window._ai_transcript] == [
            "user", "assistant", "user", "assistant"]
        # Delete removes the thread and clears the open view.
        main_window._on_ai_delete_thread()
        assert main_window.ai_thread_combo.count() == 1
        assert main_window.ai_thread_combo.itemText(0) == "No saved threads"
        assert main_window._ai_transcript == []
        assert main_window._ai_thread_id is None
    finally:
        main_window.chart_data = previous_chart
        main_window._ai_transcript = []
        main_window._ai_history = []
        main_window._ai_thread_id = None
        main_window._ai_thread_title = ""
        _restore_ai_db(old_db)


def test_ai_picker_filters_by_chart(main_window, chart, tmp_path):
    """Threads are scoped to their birth chart; no chart means no history."""
    from jhora.charts.chart import ChartBuilder
    old_db = _isolate_ai_db(tmp_path, "gui-scope.db")
    previous_chart = main_window.chart_data
    try:
        main_window.chart_data = None
        main_window._refresh_ai_threads()
        assert main_window.ai_thread_combo.count() == 1
        assert main_window.ai_thread_combo.itemText(0) == \
            "No history (compute a chart first)"
        # Persist one thread under the fixture chart.
        main_window.chart_data = chart
        main_window._ai_history = [
            {"role": "user", "content": "Career?"},
            {"role": "assistant", "content": "Mars tenth."},
        ]
        main_window._ai_transcript = list(main_window._ai_history)
        main_window._ai_thread_id = None
        main_window._persist_ai_thread()
        assert main_window.ai_thread_combo.count() == 1
        assert main_window.ai_thread_combo.itemData(0) is not None
        # Switching charts (as _on_calculate does) hides it and clears view.
        other = ChartBuilder().build(1973, 3, 13, 13.9, 45.41, 11.88,
                                     tz="+0100")
        main_window.chart_data = other
        main_window._reset_ai_thread_view()
        assert main_window.ai_thread_combo.count() == 1
        assert main_window.ai_thread_combo.itemText(0) == "No saved threads"
        assert main_window._ai_transcript == []
        # Switching back reveals it again.
        main_window.chart_data = chart
        main_window._refresh_ai_threads()
        assert main_window.ai_thread_combo.count() == 1
        assert main_window.ai_thread_combo.itemData(0) is not None
    finally:
        main_window.chart_data = previous_chart
        main_window._ai_transcript = []
        main_window._ai_history = []
        main_window._ai_thread_id = None
        main_window._ai_thread_title = ""
        _restore_ai_db(old_db)


def test_teach_transcript_appends_two_turns_with_sources(main_window):
    """Two completed lessons render oldest-first, each with its Sources block,
    and the canonical worker history wins over streamed tail text."""

    class _FakeTeachWorker:
        result_reset = False
        result_history = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "Canonical A1"},
        ]
        result_sources = [{"source": "BPHS", "excerpt": "strength..."}]

    main_window._teach_transcript = []
    main_window._teach_history = []
    main_window._teach_stream = ""
    main_window._teach_thinking = False
    main_window._teach_thread_id = None
    main_window._teach_transcript.append({"role": "user", "content": "Q1"})
    main_window._teach_stream = "drifted tail"
    main_window._teacher_worker = _FakeTeachWorker()
    main_window._on_teach_done()
    assert main_window._teach_history == _FakeTeachWorker.result_history
    main_window._teach_transcript.append({"role": "user", "content": "Q2"})
    main_window._teach_transcript.append({"role": "assistant", "content": "A2"})
    main_window._render_teach_output()
    html = main_window.teach_output.toHtml()
    positions = [html.find(s) for s in
                 ("Q1", "Canonical A1", "BPHS", "Q2", "A2")]
    assert all(p >= 0 for p in positions), "turns + sources visible"
    assert positions == sorted(positions), "oldest-first order"
    assert "drifted tail" not in html, "canonical history wins"
    main_window._teach_transcript = []
    main_window._teach_history = []
    main_window._teacher_worker = None


def test_teach_compaction_renders_divider_keeps_lesson(main_window, chart,
                                                       tmp_path):
    """An over-budget turn inserts a divider above the fresh exchange while
    prior exchanges stay visible, and the meter shows live numbers."""
    from jhora.core import database as db
    old_db_path = db._db_path
    db.set_db_path(str(tmp_path / "gui-teach-divider.db"))

    class _FakeTeachResetWorker:
        result_reset = True
        result_history = [
            {"role": "user", "content": "new Q"},
            {"role": "assistant", "content": "fresh A"},
        ]
        result_sources = []

    previous_chart = main_window.chart_data
    main_window.chart_data = chart
    main_window._teach_transcript = [
        {"role": "user", "content": "old Q"},
        {"role": "assistant", "content": "old A"},
        {"role": "user", "content": "new Q"},
    ]
    main_window._teach_history = [
        {"role": "user", "content": "old Q"},
        {"role": "assistant", "content": "old A"},
    ]
    main_window._teach_stream = ""
    main_window._teach_thinking = True
    main_window._teacher_worker = _FakeTeachResetWorker()
    try:
        main_window._on_teach_done()
        roles = [b["role"] for b in main_window._teach_transcript]
        assert roles == ["user", "assistant", "divider", "user", "assistant"]
        assert main_window._teach_history == \
            _FakeTeachResetWorker.result_history
        main_window._render_teach_output()
        html = main_window.teach_output.toHtml()
        positions = [html.find(s) for s in
                     ("old Q", "old A", "compacted", "new Q", "fresh A")]
        assert all(p >= 0 for p in positions), "lesson + divider visible"
        assert positions == sorted(positions), "divider sits above new turn"
        meter = main_window.teach_context_label.text()
        assert meter.startswith("Context: "), meter
        assert "%" in meter
    finally:
        main_window.chart_data = previous_chart
        main_window._teach_transcript = []
        main_window._teach_history = []
        main_window._teacher_worker = None
        main_window._teach_thread_id = None
        main_window._teach_thread_title = ""
        db.close_all()
        db._db_path = old_db_path


def _isolate_teach_db(tmp_path, name):
    from jhora.core import database as db
    old = db._db_path
    db.set_db_path(str(tmp_path / name))
    return old


def _restore_teach_db(old):
    from jhora.core import database as db
    db.close_all()
    db._db_path = old


def test_teach_newlesson_shelves_resume_restores_delete(main_window, chart,
                                                        tmp_path):
    """Full lesson lifecycle: shelve on New lesson, resume via picker,
    delete clears; second turns update the same row."""
    old_db = _isolate_teach_db(tmp_path, "gui-teach-lifecycle.db")
    previous_chart = main_window.chart_data
    main_window.chart_data = chart
    try:
        main_window._teach_history = [
            {"role": "user", "content": "Shadbala?"},
            {"role": "assistant", "content": "Sixfold."},
        ]
        main_window._teach_transcript = [
            {"role": "user", "content": "Shadbala?"},
            {"role": "assistant", "content": "Sixfold.",
             "sources": [{"source": "BPHS", "excerpt": "strength..."}]},
        ]
        main_window._teach_thread_id = None
        main_window._persist_teach_thread()
        tid = main_window._teach_thread_id
        assert tid is not None
        assert main_window.teach_thread_combo.count() == 1
        main_window._teach_history += [
            {"role": "user", "content": "Hora?"},
            {"role": "assistant", "content": "Hour lord."},
        ]
        main_window._teach_transcript += [
            {"role": "user", "content": "Hora?"},
            {"role": "assistant", "content": "Hour lord."},
        ]
        main_window._persist_teach_thread()
        assert main_window._teach_thread_id == tid
        assert main_window.teach_thread_combo.count() == 1
        main_window._on_teach_newlesson()
        assert main_window._teach_transcript == []
        assert main_window._teach_history == []
        assert main_window._teach_thread_id is None
        assert main_window.teach_thread_combo.count() == 1
        assert main_window.teach_thread_combo.currentIndex() == -1
        main_window.teach_thread_combo.setCurrentIndex(0)
        assert main_window._teach_thread_id == tid
        assert len(main_window._teach_history) == 4
        assert [b["role"] for b in main_window._teach_transcript] == [
            "user", "assistant", "user", "assistant"]
        assert main_window._teach_transcript[1]["sources"] == [
            {"source": "BPHS", "excerpt": "strength..."}]
        main_window._on_teach_delete_thread()
        assert main_window.teach_thread_combo.count() == 1
        assert main_window.teach_thread_combo.itemText(0) == \
            "No saved lessons"
        assert main_window._teach_transcript == []
        assert main_window._teach_thread_id is None
    finally:
        main_window.chart_data = previous_chart
        main_window._teach_transcript = []
        main_window._teach_history = []
        main_window._teach_thread_id = None
        main_window._teach_thread_title = ""
        _restore_teach_db(old_db)


def test_teach_picker_filters_by_chart(main_window, chart, tmp_path):
    """Lessons are scoped to their birth chart; chartless study has its own
    group; no chart means no history."""
    from jhora.charts.chart import ChartBuilder
    old_db = _isolate_teach_db(tmp_path, "gui-teach-scope.db")
    previous_chart = main_window.chart_data
    try:
        main_window.chart_data = None
        main_window._refresh_teach_threads()
        assert main_window.teach_thread_combo.count() == 1
        assert main_window.teach_thread_combo.itemText(0) == \
            "No history (compute a chart first)"
        # Chartless study thread lands in the General study group.
        main_window._teach_history = [
            {"role": "user", "content": "Kemadruma?"},
            {"role": "assistant", "content": "A yoga."},
        ]
        main_window._teach_transcript = list(main_window._teach_history)
        main_window._teach_thread_id = None
        main_window._persist_teach_thread()
        assert main_window.teach_thread_combo.count() == 1
        assert main_window.teach_thread_combo.itemText(0).startswith(
            "[Study]")
        # A chart thread joins the list; switching charts hides it.
        main_window.chart_data = chart
        main_window._teach_history = [
            {"role": "user", "content": "Shadbala?"},
            {"role": "assistant", "content": "Sixfold."},
        ]
        main_window._teach_transcript = list(main_window._teach_history)
        main_window._teach_thread_id = None
        main_window._persist_teach_thread()
        assert main_window.teach_thread_combo.count() == 2
        other = ChartBuilder().build(2026, 7, 7, 10.5, lat=13.08,
                                     lon=80.27, tz="+0530")
        assert other is not chart
        main_window.chart_data = other
        main_window._reset_teach_thread_view()
        assert main_window.teach_thread_combo.count() == 1
        assert main_window.teach_thread_combo.itemText(0).startswith(
            "[Study]")
        # Switching back reveals the chart thread again.
        main_window.chart_data = chart
        main_window._refresh_teach_threads()
        assert main_window.teach_thread_combo.count() == 2
    finally:
        main_window.chart_data = previous_chart
        main_window._teach_transcript = []
        main_window._teach_history = []
        main_window._teach_thread_id = None
        main_window._teach_thread_title = ""
        _restore_teach_db(old_db)


def test_muhurta_choghadiya_button_shows_slots(main_window):
    """The Choghadiya button on the Muhurta tab populates a 16-row table."""
    main_window._get_muhurta_inputs = lambda: (
        datetime.datetime(2026, 9, 3), 5.5, 22.5726, 88.3639,
    )
    main_window._on_muhurta_choghadiya()
    assert main_window.muhurta_table.rowCount() == 16, (
        "Choghadiya table should have 16 rows (8 day + 8 night)"
    )
    headers = [main_window.muhurta_table.horizontalHeaderItem(i).text()
               for i in range(main_window.muhurta_table.columnCount())]
    assert "Slot" in headers and "Rating" in headers and "Lord" in headers
    # First row should be a Day slot, row 9 a Night slot
    assert main_window.muhurta_table.item(0, 1).text() == "Day"
    assert main_window.muhurta_table.item(8, 1).text() == "Night"


def test_muhurta_adjuncts_button_shows_windows_and_grades(main_window, chart):
    """The Adjuncts button renders windows/segments and native Bala grades."""
    previous_chart = main_window.chart_data
    main_window.chart_data = chart
    main_window._get_muhurta_inputs = lambda: (
        datetime.datetime(2026, 9, 16), 5.5, 13.0827, 80.2707,
    )
    try:
        main_window._on_muhurta_adjuncts()
        headers = [main_window.muhurta_table.horizontalHeaderItem(i).text()
                   for i in range(main_window.muhurta_table.columnCount())]
        assert headers == ["Item", "Start", "End", "Detail"]
        items = [main_window.muhurta_table.item(row, 0).text()
                 for row in range(main_window.muhurta_table.rowCount())]
        assert "Sunrise" in items
        assert "DurMuhurta1" in items
        assert "Varjya1" in items
        assert any(item.startswith("Panchaka ") for item in items)
        detail = main_window.muhurta_detail.toPlainText()
        assert "Chandra Bala:" in detail
        assert "Tara Bala:" in detail
        assert "saved birth chart Moon" in detail
    finally:
        main_window.chart_data = previous_chart
