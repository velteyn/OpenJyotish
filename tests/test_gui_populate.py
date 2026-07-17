"""GUI populate tests — exercises every MainWindow populate method.

Uses QApplication with offscreen platform so it runs without a display.
Catches ALL attribute errors, unpacking errors, NameErrors etc. in one run.
"""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

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
    """All Settings tab widgets exist."""
    assert hasattr(main_window, 'ai_settings_provider')
    assert hasattr(main_window, 'ai_settings_model')
    assert hasattr(main_window, 'ai_settings_check')
    assert hasattr(main_window, 'ai_settings_status')
    assert hasattr(main_window, 'ai_vdb_build')
    assert hasattr(main_window, 'ai_vdb_rebuild')
    assert hasattr(main_window, 'ai_vdb_progress')


def test_ai_chat_buttons_created(main_window):
    """AI Chat buttons exist."""
    assert hasattr(main_window, 'ai_interpret_btn')
    assert hasattr(main_window, 'ai_remedy_btn')
    assert hasattr(main_window, 'ai_ask_btn')


def test_ai_settings_provider_defaults(main_window):
    """Provider defaults to lmstudio."""
    assert main_window.ai_settings_provider.currentText() == "lmstudio"


def test_ai_settings_provider_change(main_window):
    """Changing provider updates model field."""
    main_window.ai_settings_provider.setCurrentText("ollama")
    assert "llama" in main_window.ai_settings_model.text().lower()


def test_ai_chat_status_exists(main_window):
    """Status bar in AI Chat tab exists."""
    assert hasattr(main_window, 'ai_chat_status')
    assert "not connected" in main_window.ai_chat_status.text().lower()


def test_old_provider_widgets_removed(main_window):
    """Old ai_provider/model widgets from Chat tab are gone."""
    assert not hasattr(main_window, 'ai_provider')
    assert not hasattr(main_window, 'ai_model')
