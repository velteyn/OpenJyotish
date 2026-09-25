"""Tests for the dasa timeline widget — labels, height, expansion."""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtWidgets import QApplication

from jhora.charts.chart import ChartBuilder
from jhora.ui.dasa_timeline_widget import DasaTimelineWidget, _label_pen


@pytest.fixture(scope="module")
def _qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="module")
def chart():
    b = ChartBuilder()
    return b.build(1970, 4, 4, 17 + 48 / 60 + 20 / 3600, 13.08, 80.27,
                   tz="+0530")


@pytest.fixture(scope="module")
def widget(_qapp, chart):
    w = DasaTimelineWidget()
    w.resize(1100, 400)
    w.set_chart(chart)
    return w


class TestTimeline:
    def test_label_contrast(self):
        assert _label_pen("#e0e0e0").name() == "#111111"  # pale Moon
        assert _label_pen("#3b82f6").name() == "#ffffff"  # Saturn blue
        assert _label_pen("#eab308").name() == "#111111"  # Jupiter gold

    def test_height_fits_rows(self, widget):
        n = len(widget._mds)
        assert n == 9
        assert widget.minimumHeight() >= 10 + n * 26

    def test_expand_grows(self, widget):
        base = widget.minimumHeight()
        widget._expanded_md_index = 0
        widget._update_height()
        assert widget.minimumHeight() > base
        widget._expanded_md_index = None
        widget._update_height()
        assert widget.minimumHeight() == base

    def test_renders(self, widget):
        assert widget.grab() is not None
