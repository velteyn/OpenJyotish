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
    main_window._ai_buffer = "[Asking: q]\n\n"
    main_window._ai_thinking = True
    main_window._render_ai_output()
    html = main_window.ai_output.toHtml()
    assert "Thinking" in html or "⏳" in html

    main_window._on_ai_token("The Moon in Aries ")
    assert main_window._ai_thinking is False
    main_window._render_ai_output()
    html = main_window.ai_output.toHtml()
    assert "The Moon in Aries" in html


def test_thinking_indicator_clears_on_done(main_window):
    main_window._ai_buffer = "[Asking: q]\n\n"
    main_window._ai_thinking = True
    main_window._on_ai_done()
    assert main_window._ai_thinking is False


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
