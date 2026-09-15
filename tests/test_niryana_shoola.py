"""Tests for Niryana-Shoola dasa.

Fixture expectations follow PVR's textbook rule (stronger of 2nd/8th,
forward iff odd, fixed modality years) on the 1990 Bangalore fixture;
the ref_chart cases assert structural invariants instead.
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.niryana_shoola import NiryanaShoolaDasa


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


class TestFixture:
    def test_sequence_and_durations(self):
        # 8th Capricorn (3 occupants) beats 2nd Cancer (1); Capricorn
        # 1-based even → reverse.
        cd = _chart_1990()
        periods = NiryanaShoolaDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Capricorn", "Sagittarius", "Scorpio", "Libra",
            "Virgo", "Leo", "Cancer", "Gemini",
            "Taurus", "Aries", "Pisces", "Aquarius"]
        assert _durs(periods) == [7, 9, 8, 7, 9, 8, 7, 9, 8, 7, 9, 8]
        assert sum(_durs(periods)) == 96

    def test_tree_integrity(self):
        cd = _chart_1990()
        periods = NiryanaShoolaDasa().compute(cd.julian_day, _dict(cd))
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd
        for md in periods:
            total = sum(ad.duration_years for ad in md.sub_periods)
            assert total == pytest.approx(md.duration_years)
            assert md.sub_periods[0].lord_name == md.lord_name


class TestRefChartStructural:
    """Second chart (1970 Chennai): invariants, not hardcoded sequences."""

    def test_twelve_contiguous_96(self, ref_chart):
        cd, d = ref_chart, _dict(ref_chart)
        periods = NiryanaShoolaDasa().compute(cd.julian_day, d)
        assert len(periods) == 12
        assert sum(_durs(periods)) == 96
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd
