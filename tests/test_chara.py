"""Tests for Chara dasa (rewritten to the Rao 9th-from-lagna rule).

The 1990 Bangalore fixture expectations were derived from the classical
rules (see ``jhora.dasas.chara``) and the direction table checked
against the Savya/Apasavya lagna groups on all 12 lagnas; the ref_chart
cases assert structural invariants instead.
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.chara import CharaDasa
from jhora.dasas.jaimini_common import chara_direction


def _chart_1990():
    b = ChartBuilder()
    return b.build(1990, 1, 15, 17.5, 12.9716, 77.5946, tz="-5.5")


def _dict(cd):
    return {"planets": {g: {"longitude": p.longitude}
                        for g, p in cd.planets.items()},
            "lagna_lon": cd.ascendant}


def _lords(periods):
    return [p.lord_name for p in periods]


def _durs(periods):
    return [p.duration_years for p in periods]


class TestDirectionTable:
    def test_all_twelve_lagnas(self):
        # Savya (forward): Aries, Leo, Virgo, Libra, Aquarius, Pisces.
        # Apasavya (reverse): Taurus, Gemini, Cancer, Scorpio,
        # Sagittarius, Capricorn.
        for lag in (0, 4, 5, 6, 10, 11):
            assert chara_direction(lag) == 1, lag
        for lag in (1, 2, 3, 7, 8, 9):
            assert chara_direction(lag) == -1, lag


class TestFixture:
    def test_reverse_sequence_from_gemini(self):
        # Gemini lagna, 9th Aquarius not odd-footed → reverse.
        cd = _chart_1990()
        periods = CharaDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Gemini", "Taurus", "Aries", "Pisces",
            "Aquarius", "Capricorn", "Sagittarius", "Scorpio",
            "Libra", "Virgo", "Leo", "Cancer"]
        assert len(set(_lords(periods))) == 12

    def test_durations_and_total(self):
        # Scorpio runs 8 via Ketu (Rao own-sign exception, forward
        # footed count minus one); cross-checked against Pythe tradition.
        cd = _chart_1990()
        periods = CharaDasa().compute(cd.julian_day, _dict(cd))
        assert _durs(periods) == [6, 8, 7, 9, 1, 1, 6, 8, 3, 9, 7, 11]
        assert sum(_durs(periods)) == 76

    def test_contiguous_from_birth(self):
        cd = _chart_1990()
        periods = CharaDasa().compute(cd.julian_day, _dict(cd))
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd

    def test_antardasas_follow_cycle_direction(self):
        cd = _chart_1990()
        periods = CharaDasa().compute(cd.julian_day, _dict(cd))
        md = periods[0]  # Gemini, reverse cycle
        assert [a.lord_name for a in md.sub_periods[:3]] == [
            "Gemini", "Taurus", "Aries"]
        total = sum(ad.duration_years for ad in md.sub_periods)
        assert total == pytest.approx(md.duration_years)


class TestRefChartStructural:
    """Second chart (1970 Chennai): invariants, not hardcoded sequences."""

    def test_twelve_distinct_contiguous(self, ref_chart):
        from jhora.types.rasi import Rasi
        cd, d = ref_chart, _dict(ref_chart)
        periods = CharaDasa().compute(cd.julian_day, d)
        assert len(set(_lords(periods))) == 12
        assert periods[0].lord_name == Rasi.from_longitude(
            cd.ascendant).full_name
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd

    def test_total_matches_cycle(self, ref_chart):
        from jhora.dasas.jaimini_common import (
            chara_cycle_years, normalize_planets, planet_signs)
        cd, d = ref_chart, _dict(ref_chart)
        periods = CharaDasa().compute(cd.julian_day, d)
        planets = normalize_planets(d["planets"])
        assert sum(_durs(periods)) == sum(
            chara_cycle_years(planet_signs(planets)))
