"""Tests for Dasa Sandhi — 10% rule on synthetic + real MD lists."""

from types import SimpleNamespace

from jhora.calc.dasa_sandhi import SANDHI_FRACTION, sandhi_periods
from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.types.dasa import PeriodLevel as PL


def _md(lord, start, years, ypd=365.2425):
    return SimpleNamespace(lord_name=lord, start_jd=start,
                           end_jd=start + years * ypd,
                           duration_years=years)


class TestRule:
    def test_ketu_venus_textbook(self):
        # 10% of 7y + 10% of 20y = 0.7 + 2.0 = 2.7y (~2y9m).
        (s,) = sandhi_periods([_md("Ketu", 0.0, 7.0),
                               _md("Venus", 7 * 365.2425, 20.0)])
        assert s["outgoing"] == "Ketu" and s["incoming"] == "Venus"
        assert s["start_jd"] == 7 * 365.2425 - 0.7 * 365.2425
        assert s["end_jd"] == 7 * 365.2425 + 2.0 * 365.2425
        assert abs(s["duration_years"] - 2.7) < 1e-9
        assert SANDHI_FRACTION == 0.10

    def test_chain(self):
        mds = [_md("A", 0.0, 10.0), _md("B", 3652.425, 10.0),
               _md("C", 7304.85, 10.0)]
        out = sandhi_periods(mds)
        assert [(s["outgoing"], s["incoming"]) for s in out] == [
            ("A", "B"), ("B", "C")]

    def test_single_no_junction(self):
        assert sandhi_periods([_md("A", 0.0, 10.0)]) == []
        assert sandhi_periods([]) == []


class TestVimsottari:
    def test_jalkot_first_junction(self):
        cd = ChartBuilder().build(2001, 2, 24, 6 + 11 / 60,
                                  lat=18 + 38 / 60, lon=77 + 12 / 60,
                                  tz="+0530", ayanamsa="lahiri")
        d = {"planets": {g: {"longitude": p.longitude}
                         for g, p in cd.planets.items()},
             "lagna_lon": cd.ascendant}
        opts = DasaOptions(subdivision_level=PL.MAHADASA,
                           include_subperiods=False)
        mds = [p for p in VimsottariDasa(opts).compute(
            cd.julian_day, d, opts) if p.level == PL.MAHADASA]
        out = sandhi_periods(mds)
        assert len(out) == len(mds) - 1
        first = out[0]
        # Junction == next MD start; sandhi straddles it asymmetrically.
        assert first["junction_jd"] == mds[1].start_jd
        assert first["start_jd"] < first["junction_jd"] < first["end_jd"]
        # Sesham-shortened first MD: 10% of the lived balance, never
        # opening before birth.
        assert first["start_jd"] >= mds[0].start_jd == cd.julian_day
        assert abs(first["start_jd"]
                   - (mds[0].end_jd - 0.10 * mds[0].duration_years
                      * 365.2425)) < 1e-6
