"""Tests for the circular wheel — offscreen renders, no golden pixels."""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtWidgets import QApplication

from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha
from jhora.ui.wheel_widget import WheelWidget


@pytest.fixture(scope="module")
def _qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="module")
def chart():
    b = ChartBuilder()
    return b.build(2001, 2, 24, 6 + 11 / 60, 18 + 38 / 60,
                   77 + 12 / 60, tz="+0530", ayanamsa="lahiri")


@pytest.fixture(scope="module")
def widget(_qapp, chart):
    w = WheelWidget()
    w.resize(600, 600)
    w.set_chart_data(chart)
    w.set_transit_data({g: (float(g.value) * 40.0) % 360.0 for g in Graha})
    return w


class TestWheel:
    def test_renders(self, widget):
        pix = widget.grab()
        assert not pix.isNull()
        assert pix.width() == 600

    def test_empty_state(self, _qapp):
        w = WheelWidget()
        w.resize(400, 400)
        assert w.grab() is not None

    def test_toggles(self, widget):
        widget.settings.show_drishti = False
        widget.update()
        assert widget.grab() is not None
        widget.settings.show_drishti = True
        widget.settings.show_nodes = False
        widget.settings.show_transits = False
        widget.update()
        assert widget.grab() is not None
        widget.settings.show_nodes = True
        widget.settings.show_transits = True

    def test_transit_nodes_absent_ok(self, widget, chart):
        # Transit ring without nodes still renders.
        widget.set_transit_data({Graha.SUN: 10.0, Graha.MOON: 200.0})
        assert widget.grab() is not None
        widget.set_transit_data({g: (float(g.value) * 40.0) % 360.0
                                 for g in Graha})

    def test_hit_records(self, widget):
        assert widget._hit
        grahas = {g for g, _, _, _, _ in widget._hit}
        assert Graha.SUN in grahas and Graha.SATURN in grahas
        tips = [tip for _, _, _, _, tip in widget._hit]
        assert any("Jupiter" in tip for tip in tips)


@pytest.fixture(scope="module")
def main_window(_qapp):
    from jhora.ui.main_window import MainWindow
    return MainWindow()


class TestWheelPage:
    def test_nav_and_page(self, main_window):
        labels = [main_window.nav_list.item(i).text()
                  for i in range(main_window.nav_list.count())]
        assert any("Wheel" in label for label in labels)
        assert main_window.page_stack.count() == 10

    def test_populate(self, main_window, chart):
        main_window.chart_data = chart
        main_window._populate_wheel_page(chart)
        assert main_window.wheel_widget.chart_data is chart
        assert main_window.wheel_widget.transit_lons
        main_window.wheel_widget.resize(600, 600)
        assert main_window.wheel_widget.grab() is not None

    def test_settings_panel(self, main_window, chart):
        main_window.chart_data = chart
        main_window._populate_wheel_page(chart)
        main_window.wheel_zoom_slider.setValue(150)
        assert main_window.wheel_widget.settings.symbol_scale == 1.5
        main_window.wheel_signs_check.setChecked(False)
        assert not main_window.wheel_widget.settings.show_sign_colors
        main_window.wheel_signs_check.setChecked(True)
        # Transit date scrub to the great conjunction: Ju/Sa at war.
        from PyQt6.QtCore import QDate
        from jhora.calc.yuddha import separation
        main_window.wheel_transit_date.setDate(QDate(2020, 12, 21))
        lons = main_window.wheel_widget.transit_lons
        assert separation(lons[Graha.JUPITER],
                          lons[Graha.SATURN]) < 1.0
        main_window.wheel_now_btn.click()
