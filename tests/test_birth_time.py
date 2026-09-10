"""Regression: birth time fields must carry the true local clock time.

ChartData.birth_date is intentionally date-only (midnight); the exact moment
lives in julian_day. These tests pin that day/night selection and Janma
Ghatis use time_of_day_hours, not the truncated birth_date.
"""

import os
import re
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtWidgets import QApplication

from jhora.charts.chart import ChartBuilder
from jhora.calc.sahama import compute_sahamas
from jhora.types.graha import Graha


@pytest.fixture(scope="module")
def _qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="module")
def main_window(_qapp):
    from jhora.ui.main_window import MainWindow
    return MainWindow()


def _chart(hour):
    b = ChartBuilder()
    return b.build(year=2026, month=7, day=7, hour=hour,
                   lat=13.08, lon=80.27, tz="+0530")


def _planets(cd):
    return {g: {"longitude": p.longitude} for g, p in cd.planets.items()}


def _expected_sahama_lons(cd, day):
    return [s.longitude for s in compute_sahamas(cd.ascendant, _planets(cd),
                                                 day=day)]


def test_time_of_day_hours_matches_birth_time():
    assert abs(_chart(10.5).time_of_day_hours - 10.5) < 1e-6
    assert abs(_chart(2.0).time_of_day_hours - 2.0) < 1e-6
    # The raw birth_date field stays date-only (midnight) by design.
    assert _chart(10.5).birth_date.hour == 0


def test_json_export_sahamas_follow_true_day_night():
    from jhora.ai.json_export import chart_to_json
    day_cd, night_cd = _chart(10.5), _chart(2.0)
    day_got = [s["longitude"] for s in chart_to_json(day_cd)["sahamas"]]
    night_got = [s["longitude"] for s in chart_to_json(night_cd)["sahamas"]]
    assert day_got == [round(v, 2) for v in _expected_sahama_lons(day_cd, True)]
    assert night_got == [round(v, 2)
                         for v in _expected_sahama_lons(night_cd, False)]
    assert day_got != [round(v, 2)
                       for v in _expected_sahama_lons(day_cd, False)]


def _snapshot_sahama_lons(cd):
    from jhora.ai.analysis import build_analysis_text
    lines = build_analysis_text(cd).splitlines()
    start = next(i for i, ln in enumerate(lines)
                 if "Sahamas (sensitive points):" in ln)
    lons = []
    for ln in lines[start + 1:]:
        if ln.startswith("---"):
            break
        m = re.search(r"([\d.]+)°", ln)
        if m:
            lons.append(float(m.group(1)))
    return lons


def test_analysis_snapshot_sahamas_follow_true_day_night():
    day_cd, night_cd = _chart(10.5), _chart(2.0)
    assert _snapshot_sahama_lons(day_cd) == [
        round(v, 1) for v in _expected_sahama_lons(day_cd, True)]
    assert _snapshot_sahama_lons(night_cd) == [
        round(v, 1) for v in _expected_sahama_lons(night_cd, False)]


def test_gui_sahama_table_follows_true_day_night(main_window):
    day_cd, night_cd = _chart(10.5), _chart(2.0)
    main_window._populate_arudha_table(day_cd)
    day_got = [float(main_window.sahama_table.item(r, 2).text().rstrip("°"))
               for r in range(main_window.sahama_table.rowCount())]
    main_window._populate_arudha_table(night_cd)
    night_got = [float(main_window.sahama_table.item(r, 2).text().rstrip("°"))
                 for r in range(main_window.sahama_table.rowCount())]
    assert day_got == [round(v, 2) for v in _expected_sahama_lons(day_cd, True)]
    assert night_got == [round(v, 2)
                         for v in _expected_sahama_lons(night_cd, False)]


def _ghatis(main_window, cd):
    main_window._populate_cons_natal_panel(cd)
    text = main_window.cons_natal_panel.toPlainText()
    m = re.search(r"Janma Ghatis:\s*([\d.]+)", text)
    assert m, "Ghatis line missing from natal panel"
    return float(m.group(1))


def test_janma_ghatis_formula_uses_birth_time():
    # Pure formula path: an 8.5 h birth-time shift is 21.25 ghatis from any
    # common sunrise reference (live panel display needs swe rise_trans,
    # which this environment's pyswisseph rejects — see report).
    from jhora.ui.main_window import _janma_ghatis
    for sunrise in (5.5, 6.0, 6.5):
        shift = (_janma_ghatis(10.5, sunrise)
                 - _janma_ghatis(2.0, sunrise)) % 60.0
        assert abs(shift - 21.25) < 1e-9


def test_natal_panel_renders_ghatis_line(main_window):
    assert _ghatis(main_window, _chart(10.5)) >= 0.0


def test_pranapada_vighati_use_true_birth_time():
    # Definition conformance against the true local time, plus a shift check:
    # same day/place 8.5 h apart must differ markedly (the old midnight code
    # kept them within a degree of each other).
    from jhora.calc.special_lagnas import (
        pranapada_lagna, vighati_lagna, _sunrise_approx)
    day_cd, night_cd = _chart(10.5), _chart(2.0)
    for cd in (day_cd, night_cd):
        sun = cd.planet(Graha.SUN).longitude
        from_sr = (cd.time_of_day_hours - _sunrise_approx(cd) + 24) % 24
        assert abs(pranapada_lagna(cd)
                   - (sun + from_sr / 0.4 * 6) % 360) < 1e-6
        assert abs(vighati_lagna(cd)
                   - (sun + from_sr * 60 * 0.1) % 360) < 1e-6
    d_prana = (pranapada_lagna(day_cd) - pranapada_lagna(night_cd)) % 360.0
    d_vig = (vighati_lagna(day_cd) - vighati_lagna(night_cd)) % 360.0
    assert d_prana > 90.0
    assert d_vig > 90.0
