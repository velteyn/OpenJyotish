"""Tests for Sudarshana Chakra dasa."""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.sudarshana import SudarshanaDasa
from jhora.types.rasi import Rasi


def _chart():
    cd = ChartBuilder().build(1990, 1, 15, 17.5, 12.9716, 77.5946, tz="+0530")
    d = {"planets": {g: {"longitude": p.longitude}
                     for g, p in cd.planets.items()},
         "lagna_lon": cd.ascendant}
    return cd, d


class TestSudarshana:
    def test_mahadasas_are_the_lagna_chakra_one_year_each(self):
        cd, d = _chart()
        lagna = int(cd.ascendant // 30) % 12
        periods = SudarshanaDasa().compute(cd.julian_day, d, DasaOptions())
        assert [p.lord_index - 100 for p in periods] == \
            [(lagna + k) % 12 for k in range(12)]
        assert all(p.duration_years == 1.0 for p in periods)
        for a, b in zip(periods, periods[1:]):
            assert abs(a.end_jd - b.start_jd) < 1e-6

    def test_antardasas_equal_and_from_the_lord_sign(self):
        cd, d = _chart()
        periods = SudarshanaDasa().compute(cd.julian_day, d, DasaOptions())
        md = periods[0]
        assert len(md.sub_periods) == 12
        assert md.sub_periods[0].duration_years == pytest.approx(
            md.duration_years / 12, rel=1e-9)
        # Gemini's lord is Mercury; in 1990 it sits in Sagittarius (8).
        assert md.sub_periods[0].lord_name == Rasi(8).full_name
        # The reference builder assembles only MD and AD: no deeper level.
        assert all(p.sub_periods is None for p in md.sub_periods)

    def test_ad_from_md_sign_option(self):
        cd, d = _chart()
        periods = SudarshanaDasa().compute(
            cd.julian_day, d, DasaOptions(sudarshana_ad_from_lord=False))
        md = periods[0]
        assert md.sub_periods[0].lord_index - 100 == md.lord_index - 100
