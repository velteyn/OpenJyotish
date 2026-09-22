"""Rasi-Bhukta Vimsottari dasa — Vimsottari MDs with rasi antardasas."""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.rasi_bhukta import RasiBhuktaVimsottariDasa
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


def _chart():
    cd = ChartBuilder().build(1990, 1, 15, 17.5, 12.9716, 77.5946, tz="+0530")
    d = {"planets": {g: {"longitude": p.longitude}
                     for g, p in cd.planets.items()},
         "lagna_lon": cd.ascendant}
    return cd, d


class TestRasiBhuktaVimsottari:
    def test_mahadasas_match_vimsottari(self):
        cd, d = _chart()
        base = VimsottariDasa().compute(cd.julian_day, d, DasaOptions())
        rasi = RasiBhuktaVimsottariDasa().compute(cd.julian_day, d,
                                                  DasaOptions())
        assert [p.lord_name for p in rasi] == [p.lord_name for p in base]
        assert [round(p.duration_years, 6) for p in rasi] == \
            [round(p.duration_years, 6) for p in base]

    def test_antardasas_are_twelve_rasis_from_the_lord_sign(self):
        cd, d = _chart()
        periods = RasiBhuktaVimsottariDasa().compute(cd.julian_day, d,
                                                     DasaOptions())
        for md in periods:
            lord_sign = int(d["planets"][Graha(md.lord_index)]["longitude"]
                            // 30) % 12
            assert [s.lord_name for s in md.sub_periods] == \
                [Rasi((lord_sign + k) % 12).full_name for k in range(12)]
            for s in md.sub_periods:
                assert s.duration_years == pytest.approx(
                    md.duration_years / 12, rel=1e-9)
            assert sum(s.duration_years for s in md.sub_periods) == \
                pytest.approx(md.duration_years, rel=1e-9)

    def test_contiguous(self):
        cd, d = _chart()
        periods = RasiBhuktaVimsottariDasa().compute(cd.julian_day, d,
                                                     DasaOptions())
        for md in periods:
            for a, b in zip(md.sub_periods, md.sub_periods[1:]):
                assert a.end_jd == b.start_jd
