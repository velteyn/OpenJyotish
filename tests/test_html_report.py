"""Tests for the HTML chart report (parity with the traditional report)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from jhora.charts.chart import ChartBuilder


def _chart():
    b = ChartBuilder()
    return b.build(1995, 10, 31, 12 + 25 / 60 + 30 / 3600,
                   19.18, 72.50, tz="+0530")


def _html():
    from jhora.export.report import _build_html
    return _build_html(_chart(), "full")


def test_title_and_meta():
    html = _html()
    assert "OpenJyotish Chart Report" in html
    assert "Jhora Chart Report" not in html
    assert "19.18" in html and "72.50" in html
    assert "Tithi" in html and "Sunrise" in html and "Dasa balance" in html


def test_navamsa_is_real_chart():
    """The D-9 image must differ from D-1 (was a mislabeled duplicate)."""
    import base64
    import re
    from PyQt6.QtCore import QBuffer, QIODevice
    from jhora.export.traditional import (
        render_chart_card, _chart_occupants, _navamsa_occupants)
    from jhora.types.rasi import Rasi

    def _png(lagna_rasi, houses):
        img = render_chart_card(lagna_rasi, houses, size=200, dark=True)
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        data = bytes(buf.data().data())
        buf.close()
        return base64.b64encode(data).decode("ascii")

    cd = _chart()
    d1 = _png(Rasi.from_longitude(cd.ascendant), _chart_occupants(cd))
    nl, nh = _navamsa_occupants(cd)
    assert nl.full_name == "Capricorn"
    d9 = _png(nl, nh)
    assert d1 != d9
    assert nh[1] == ["Ju", "Ur"]  # matches the reference Reddit chart


def test_strength_and_av_sections():
    html = _html()
    assert "Bhava Bala" in html
    assert "Ashtakavarga" in html
    assert "SAV total 337" in html


def test_export_writes_file(tmp_path):
    from jhora.export.report import generate_chart_report
    out = str(tmp_path / "rep.html")
    assert generate_chart_report(_chart(), out) == out
    assert os.path.getsize(out) > 50_000
