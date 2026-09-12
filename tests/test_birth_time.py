"""Regression: birth time fields must carry the true local clock time.

ChartData.birth_date is intentionally date-only (midnight); the exact moment
lives in julian_day. These tests pin that day/night selection and Janma
Ghatis use time_of_day_hours, not the truncated birth_date.
"""

import os
import re
import sys
from datetime import datetime

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
    # The birth_date field carries the wall-clock birth time.
    assert _chart(10.5).birth_date.hour == 10
    assert _chart(10.5).birth_date.minute == 30


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


def test_natal_panel_live_sun_times(main_window):
    # The panel now resolves through the canonical source: live Sunrise,
    # and Ghatis shifting 21.25 per 8.5 h of birth time.
    from jhora.calc.muhurta import sunrise_sunset_hours
    from jhora.charts.chart import ChartBuilder
    day_cd, night_cd = _chart(10.5), _chart(2.0)
    main_window._populate_cons_natal_panel(day_cd)
    text = main_window.cons_natal_panel.toPlainText()
    m = re.search(r"Sunrise:\s*(\d+):(\d+)", text)
    assert m, "live Sunrise missing from natal panel"
    shown = int(m.group(1)) + int(m.group(2)) / 60.0
    sr, _ss = sunrise_sunset_hours(
        day_cd.birth_date, 13.08, 80.27,
        -ChartBuilder._parse_tz("+0530"))
    assert abs(shown - sr) < 2 / 60.0
    day_g = _ghatis(main_window, day_cd)
    night_g = _ghatis(main_window, night_cd)
    assert day_g > 0.0
    assert abs((day_g - night_g) % 60.0 - 21.25) < 0.05


def test_shadbala_dawn_noon_true_sun_phases():
    # Dawn (just after true sunrise): first day hora lord Sun scores, first
    # tribhaga period lord Moon scores. Solar noon: Sun Nathonnata peaks.
    from jhora.calc.muhurta import sunrise_sunset_hours
    from jhora.calc.shadbala import ShadbalaComputer
    from jhora.charts.chart import ChartBuilder
    from jhora.types.graha import Graha
    sr, ss = sunrise_sunset_hours(datetime(2026, 7, 7), 13.08, 80.27, 5.5)
    b = ChartBuilder()
    dawn = b.build(2026, 7, 7, sr + 0.3, lat=13.08, lon=80.27, tz="+0530")
    noon = b.build(2026, 7, 7, (sr + ss) / 2.0, lat=13.08, lon=80.27,
                   tz="+0530")
    assert ShadbalaComputer(dawn).compute_one(
        Graha.SUN).kala["hora"].virupa == 60
    assert ShadbalaComputer(dawn).compute_one(
        Graha.MOON).kala["tribhaga"].virupa == 60
    assert ShadbalaComputer(noon).compute_one(
        Graha.SUN).kala["nathonnatha"].virupa == pytest.approx(60)


def test_gui_save_load_tz_round_trip(main_window, tmp_path):
    """GUI save stores east-positive tz; refilling the form shows +5.5."""
    from PyQt6.QtCore import QDate, QTime
    from jhora.core import database as db
    from jhora.io.jhd_parser import JhdData, JhdFormat
    old_db = db._db_path
    db.set_db_path(str(tmp_path / "gui-tz.db"))
    try:
        main_window.date_input.setDate(QDate(2026, 7, 7))
        main_window.time_input.setTime(QTime(10, 30))
        main_window.tz_input.setText("+0530")
        main_window.lat_input.setText("13.08")
        main_window.lon_input.setText("80.27")
        main_window.city_input.setText("Chennai")
        main_window._on_file_save()
        row = db.get_db().execute(
            "SELECT time_hours, tz_offset FROM charts ORDER BY id DESC "
            "LIMIT 1").fetchone()
        assert abs(row["time_hours"] - 10.5) < 1e-9
        assert abs(row["tz_offset"] - 5.5) < 1e-9
        main_window._fill_form_from_jhd(JhdData(
            filename="x.jhd", format=JhdFormat.BIRTH_CITY,
            day=7, month=7, year=2026, time_hours=row["time_hours"],
            tz_offset=row["tz_offset"], longitude=80.27, latitude=13.08,
            city="Chennai", country=""))
        assert main_window.tz_input.text() == "+5.5"
    finally:
        db.close_all()
        db._db_path = old_db


def test_pranapada_vighati_use_true_birth_time():
    # Definition conformance against the true local time, plus a shift check:
    # same day/place 8.5 h apart must differ markedly (the old midnight code
    # kept them within a degree of each other).
    from jhora.calc.special_lagnas import pranapada_lagna, vighati_lagna
    from jhora.calc.muhurta import sunrise_sunset_hours
    from jhora.charts.chart import ChartBuilder
    day_cd, night_cd = _chart(10.5), _chart(2.0)
    for cd in (day_cd, night_cd):
        sun = cd.planet(Graha.SUN).longitude
        sr, _ss = sunrise_sunset_hours(
            cd.birth_date, cd.latitude, cd.longitude,
            -ChartBuilder._parse_tz(cd.timezone))
        from_sr = (cd.time_of_day_hours - sr + 24) % 24
        assert abs(pranapada_lagna(cd)
                   - (sun + from_sr / 0.4 * 6) % 360) < 1e-6
        assert abs(vighati_lagna(cd)
                   - (sun + from_sr * 60 * 0.1) % 360) < 1e-6
    d_prana = (pranapada_lagna(day_cd) - pranapada_lagna(night_cd)) % 360.0
    d_vig = (vighati_lagna(day_cd) - vighati_lagna(night_cd)) % 360.0
    assert d_prana > 90.0
    assert d_vig > 90.0
