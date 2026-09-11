"""Dashboard regression tests — headless (offscreen) MainWindow.

Locks the fixes for the user's 1973-03-13 Padua chart:
  1. "Next Mahadasha" must not skip the immediately following MD
     (strict `>` on contiguous boundaries showed Sun 2051 instead of
     Venus 2031 while in Ketu MD).
  2. Sade Sati must use TRANSIT Saturn vs natal Moon, never natal Saturn.
  3. Retrograde Watch must use TRANSIT retro status, never natal.

Expectations are derived independently (engine + gochara) at test time,
so the tests hold regardless of the current date.
"""

import sys
from datetime import datetime

import pytest
from PyQt6.QtWidgets import QApplication

from jhora.charts.chart import ChartBuilder
from jhora.calc.gochara import compute_transits
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.types.graha import Graha


@pytest.fixture(scope="module")
def _qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="module")
def window(_qapp):
    from jhora.ui.main_window import MainWindow
    return MainWindow()


@pytest.fixture(scope="module")
def chart():
    return ChartBuilder().build(1973, 3, 13, 13 + 55 / 60,
                                lat=45.4130, lon=11.8806, tz="+0100")


@pytest.fixture(scope="module")
def dashboard_texts(window, chart):
    window._populate_dashboard(chart)
    return (window.dash_upcoming.toPlainText(),
            window.dash_keydates.toPlainText())


def _periods(chart):
    dasa = VimsottariDasa()
    cd = {"planets": {g.value: {"longitude": p.longitude}
                      for g, p in chart.planets.items()},
          "lagna_lon": chart.ascendant}
    return dasa.compute(chart.julian_day, cd)


def test_next_mahadasa_is_immediately_following(chart, dashboard_texts):
    upcoming, _ = dashboard_texts
    now = datetime.now()
    periods = _periods(chart)
    current = next(p for p in periods if p.start_date <= now <= p.end_date)
    expected = next(p for p in periods if p.start_date >= current.end_date)
    assert f"Next Mahadasha: {expected.lord_name}" in upcoming


def test_sade_sati_uses_transit_saturn(chart, dashboard_texts):
    _, keydates = dashboard_texts
    tr = compute_transits(chart)
    sat_rasi = next(e for e in tr.entries if e.graha == Graha.SATURN).transit_rasi
    moon_rasi = int(chart.planet(Graha.MOON).longitude / 30)
    ss = [(moon_rasi - 1) % 12, moon_rasi, (moon_rasi + 1) % 12]
    if sat_rasi in ss:
        pos = ["12th from Moon", "1st from Moon (peak)",
               "2nd from Moon"][ss.index(sat_rasi)]
        assert f"IN Sade Sati ({pos})" in keydates
    else:
        assert "IN Sade Sati" not in keydates
        assert "Sade Sati in" in keydates


def test_retro_watch_uses_transit_status(chart, dashboard_texts):
    _, keydates = dashboard_texts
    tr = compute_transits(chart)
    watched = (Graha.MERCURY, Graha.VENUS, Graha.MARS,
               Graha.JUPITER, Graha.SATURN)
    retro = {e.graha for e in tr.entries
             if e.graha in watched and e.is_retrograde}
    for g in watched:
        line = f"{g.short_name} is currently RETROGRADE"
        if g in retro:
            assert line in keydates
        else:
            assert line not in keydates
    if not retro:
        assert "No major planet retrograde" in keydates
