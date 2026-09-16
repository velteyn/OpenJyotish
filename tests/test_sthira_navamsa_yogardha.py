"""Tests for Sthira, Navamsa and Yogardha dasas.

Sthira expectations are triple-confirmed (Sastri text, PyJHora code,
fixed modality table). Yogardha durations reproduce PyJHora exactly on
the 1990 fixture. Navamsa follows the textbook Chara-on-D9 form; the
ref_chart cases assert structural invariants instead.
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.navamsa import NavamsaDasa
from jhora.dasas.sthira import SthiraDasa
from jhora.dasas.yogardha import YogardhaDasa


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


def _assert_tree(periods, birth_jd):
    assert periods[0].start_jd == birth_jd
    for a, b in zip(periods, periods[1:]):
        assert a.end_jd == b.start_jd
    for md in periods:
        total = sum(ad.duration_years for ad in md.sub_periods)
        assert total == pytest.approx(md.duration_years)
        assert md.sub_periods[0].lord_name == md.lord_name


class TestSthira:
    def test_sequence_and_durations(self):
        # Brahma Venus in Capricorn → forward; modality years.
        cd = _chart_1990()
        periods = SthiraDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Capricorn", "Aquarius", "Pisces", "Aries",
            "Taurus", "Gemini", "Cancer", "Leo",
            "Virgo", "Libra", "Scorpio", "Sagittarius"]
        assert _durs(periods) == [7, 8, 9, 7, 8, 9, 7, 8, 9, 7, 8, 9]
        assert sum(_durs(periods)) == 96

    def test_tree_integrity(self):
        cd = _chart_1990()
        _assert_tree(SthiraDasa().compute(cd.julian_day, _dict(cd)),
                     cd.julian_day)


class TestNavamsa:
    def test_sequence_and_durations(self):
        # D1 lagna lord Mercury in Sagittarius → forward from
        # Sagittarius, 9 fixed years (JHora-verified on 3 charts).
        cd = _chart_1990()
        periods = NavamsaDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Sagittarius", "Capricorn", "Aquarius", "Pisces",
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio"]
        assert _durs(periods) == [9] * 12
        assert sum(_durs(periods)) == 108

    def test_tree_integrity(self):
        cd = _chart_1990()
        _assert_tree(NavamsaDasa().compute(cd.julian_day, _dict(cd)),
                     cd.julian_day)


class TestYogardha:
    def test_sequence_and_durations(self):
        # Stronger of Gemini/Sagittarius is Sagittarius (occupancy) →
        # forward; (Chara + modality)/2 reproduces PyJHora exactly.
        cd = _chart_1990()
        periods = YogardhaDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Sagittarius", "Capricorn", "Aquarius", "Pisces",
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio"]
        assert _durs(periods) == [7.5, 4.0, 4.5, 9.0, 7.0, 8.0,
                                  7.5, 9.0, 7.5, 9.0, 5.0, 8.0]
        assert sum(_durs(periods)) == pytest.approx(86.0)

    def test_tree_integrity(self):
        cd = _chart_1990()
        _assert_tree(YogardhaDasa().compute(cd.julian_day, _dict(cd)),
                     cd.julian_day)


class TestRefChartStructural:
    """Second chart (1970 Chennai): invariants, not hardcoded sequences."""

    def test_all_twelve_and_contiguous(self, ref_chart):
        cd, d = ref_chart, _dict(ref_chart)
        for engine in (SthiraDasa(), NavamsaDasa(), YogardhaDasa()):
            periods = engine.compute(cd.julian_day, d)
            assert len(periods) == 12
            assert periods[0].start_jd == cd.julian_day
            for a, b in zip(periods, periods[1:]):
                assert a.end_jd == b.start_jd

    def test_sthira_always_96(self, ref_chart):
        cd, d = ref_chart, _dict(ref_chart)
        assert sum(_durs(
            SthiraDasa().compute(cd.julian_day, d))) == 96
