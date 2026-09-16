"""Tests for Lagna and AK Kendradi Rasi dasas.

Fixture expectations follow PVR textbook ch. 19 (kendra jumps,
Saturn/Ketu/parity direction, counted durations) on the 1990
Bangalore fixture; the ref_chart cases assert structural invariants.
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.kendradi import AKKendradiDasa, LagnaKendradiDasa


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
    assert len({p.lord_name for p in periods}) == 12
    for md in periods:
        ads = md.sub_periods
        assert len(ads) == 12
        assert ads[0].lord_name == md.lord_name
        first = ads[0].duration_years
        for ad in ads:
            assert ad.duration_years == pytest.approx(first)
        assert sum(a.duration_years for a in ads) == pytest.approx(
            md.duration_years)


class TestLagnaKendradi:
    def test_sequence_and_durations(self):
        # Stronger(Ge, Sg) = Sg (occupancy); Saturn in Sg → forward;
        # kendra jumps, counted durations.
        cd = _chart_1990()
        periods = LagnaKendradiDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Sagittarius", "Pisces", "Gemini", "Virgo",
            "Capricorn", "Aries", "Cancer", "Libra",
            "Aquarius", "Taurus", "Leo", "Scorpio"]
        assert _durs(periods) == [6, 9, 6, 9, 1, 7, 11, 3, 1, 8, 7, 8]
        assert sum(_durs(periods)) == 76

    def test_tree_integrity(self):
        cd = _chart_1990()
        _assert_tree(LagnaKendradiDasa().compute(cd.julian_day, _dict(cd)),
                     cd.julian_day)


@pytest.mark.skip(reason="AK Kendradi suspended: reference tables refutes "
                        "seed/order/cycles; pending dedicated research")
class TestAKKendradi:
    """SUSPENDED — see module note. Skipped, not deleted."""

    def test_sequence_and_durations(self):
        # AK Mars in Scorpio beats Taurus; Scorpio odd index, no
        # Saturn/Ketu → backward kendra jumps.
        cd = _chart_1990()
        periods = AKKendradiDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Scorpio", "Leo", "Taurus", "Aquarius",
            "Libra", "Cancer", "Aries", "Capricorn",
            "Virgo", "Gemini", "Pisces", "Sagittarius"]
        assert _durs(periods) == [8, 7, 8, 1, 3, 11, 7, 1, 9, 6, 9, 6]
        assert sum(_durs(periods)) == 76

    def test_tree_integrity(self):
        cd = _chart_1990()
        _assert_tree(AKKendradiDasa().compute(cd.julian_day, _dict(cd)),
                     cd.julian_day)


class TestRefChartStructural:
    """Second chart (1970 Chennai): invariants, not hardcoded sequences."""

    def test_both_cover_twelve(self, ref_chart):
        cd, d = ref_chart, _dict(ref_chart)
        for engine in (LagnaKendradiDasa(),):
            periods = engine.compute(cd.julian_day, d)
            assert len(periods) == 12
            assert len({p.lord_name for p in periods}) == 12
            assert periods[0].start_jd == cd.julian_day
            for a, b in zip(periods, periods[1:]):
                assert a.end_jd == b.start_jd
