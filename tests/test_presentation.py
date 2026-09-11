"""Unit tests for shared presentation helpers.

GUI, TUI (and CLI where applicable) must render through these instead of
re-implementing period picking, Sade Sati math, and house-index math
inline — the inline copies drifted and produced the dashboard bugs
(PR #48: skipped Venus MD, natal-based Sade Sati/retro labels).

All dates are fixed, so these tests are fully deterministic.
"""

from datetime import datetime

from jhora.calc.dasa_timeline import (current_period, next_mahadasa,
                                      upcoming_sub_periods)
from jhora.calc.gochara import sade_sati_status
from jhora.charts.chart import ChartBuilder, house_rasi_index
from jhora.dasas.vimsottari import VimsottariDasa


def _periods():
    cd = ChartBuilder().build(1973, 3, 13, 13 + 55 / 60,
                              lat=45.4130, lon=11.8806, tz="+0100")
    chart_dict = {"planets": {g.value: {"longitude": p.longitude}
                              for g, p in cd.planets.items()},
                  "lagna_lon": cd.ascendant}
    return VimsottariDasa().compute(cd.julian_day, chart_dict)


def _md(periods, name):
    return next(p for p in periods if p.lord_name == name)


class TestCurrentPeriod:
    def test_ketu_now(self):
        assert current_period(_periods(), datetime(2026, 9, 11)).lord_name == "Ketu"

    def test_marriage_date_was_mercury(self):
        assert current_period(_periods(), datetime(2008, 12, 20)).lord_name == "Mercury"

    def test_after_ketu_is_venus(self):
        assert current_period(_periods(), datetime(2031, 5, 1)).lord_name == "Venus"

    def test_outside_sequence_is_none(self):
        periods = _periods()
        assert current_period(periods, datetime(1970, 1, 1)) is None
        assert current_period(periods, datetime(2100, 1, 1)) is None

    def test_current_antardasa(self):
        ketu = _md(_periods(), "Ketu")
        assert current_period(ketu.sub_periods, datetime(2026, 9, 11)).lord_name == "Moon"
        assert current_period(ketu.sub_periods, datetime(2027, 1, 1)).lord_name == "Mars"


class TestNextMahadasa:
    def test_ketu_is_followed_by_venus(self):
        # Regression: strict > skipped Venus (starts exactly at Ketu's end).
        periods = _periods()
        nxt = next_mahadasa(periods, _md(periods, "Ketu"))
        assert nxt.lord_name == "Venus"
        assert nxt.start_date.strftime("%Y-%m-%d") == "2031-04-13"

    def test_last_md_has_no_next(self):
        periods = _periods()
        assert next_mahadasa(periods, periods[-1]) is None


class TestUpcomingSubPeriods:
    def test_order_and_default_limit(self):
        ketu = _md(_periods(), "Ketu")
        ups = upcoming_sub_periods(ketu, datetime(2026, 9, 11))
        assert [sp.lord_name for sp in ups] == ["Mars", "Rahu", "Jupiter", "Saturn"]

    def test_limit_is_honored(self):
        ketu = _md(_periods(), "Ketu")
        ups = upcoming_sub_periods(ketu, datetime(2026, 9, 11), limit=2)
        assert [sp.lord_name for sp in ups] == ["Mars", "Rahu"]


class TestSadeSatiStatus:
    def test_phases(self):
        assert sade_sati_status(2, 11) == ""          # Pisces vs Gemini Moon: none
        assert sade_sati_status(2, 1) == "12th from Moon"
        assert sade_sati_status(2, 2) == "1st from Moon (peak)"
        assert sade_sati_status(2, 3) == "2nd from Moon"

    def test_wraps_around_aries(self):
        assert sade_sati_status(0, 11) == "12th from Moon"
        assert sade_sati_status(0, 1) == "2nd from Moon"


class TestHouseRasiIndex:
    def test_cancer_lagna(self):
        assert house_rasi_index(101.33, 1) == 3    # H1 Cancer
        assert house_rasi_index(101.33, 7) == 9    # H7 Capricorn
        assert house_rasi_index(101.33, 12) == 2   # H12 Gemini

    def test_gemini_lagna(self):
        assert house_rasi_index(89.8, 1) == 2      # H1 Gemini
