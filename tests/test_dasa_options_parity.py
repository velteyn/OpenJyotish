"""Tests for the widened dasa options, per-varga Bhava Bala and parity tables."""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.narayana import NarayanaDasa
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.types.graha import Graha


def _chart_dict():
    cb = ChartBuilder()
    cb.swe.set_sidereal_mode("lahiri")
    cd = cb.build(year=1970, month=4, day=4, hour=23.3,
                  lat=13.08, lon=80.27, tz="-5.5", ayanamsa="lahiri")
    ch = {
        "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                    for g, p in cd.planets.items()},
        "lagna_lon": cd.ascendant,
        "gulika_lon": 200.0,
    }
    return cd, ch


class TestSeedPoints:
    def test_all_seeds_resolve(self):
        _cd, ch = _chart_dict()
        for var in ["moon", "lagna", "sun", "kshema", "utpanna", "adhana",
                    "devi", "brahma", "maandi", "trisphuta"]:
            lon, nak = VimsottariDasa()._seed_longitude(ch, var)
            assert 0.0 <= lon < 360.0
            assert 0 <= nak < 27

    def test_maandi_uses_gulika_longitude(self):
        _cd, ch = _chart_dict()
        lon, _ = VimsottariDasa()._seed_longitude(ch, "maandi")
        assert lon == pytest.approx(200.0)

    def test_trisphuta_is_lagna_plus_moon_plus_gulika(self):
        _cd, ch = _chart_dict()
        lon, _ = VimsottariDasa()._seed_longitude(ch, "trisphuta")
        expected = (ch["lagna_lon"] + ch["planets"][Graha.MOON]["longitude"]
                    + 200.0) % 360.0
        assert lon == pytest.approx(expected)

    def test_devi_and_brahma_offset_from_moon(self):
        _cd, ch = _chart_dict()
        moon_lon = ch["planets"][Graha.MOON]["longitude"]
        devi, _ = VimsottariDasa()._seed_longitude(ch, "devi")
        brahma, _ = VimsottariDasa()._seed_longitude(ch, "brahma")
        moon_nak = int(moon_lon // (360 / 27))
        assert devi == pytest.approx(((moon_nak + 6) % 27) * (360 / 27) + 0.001)
        assert brahma == pytest.approx(((moon_nak + 8) % 27) * (360 / 27) + 0.001)

    def test_point_seed_falls_back_without_gulika(self):
        _cd, ch = _chart_dict()
        del ch["gulika_lon"]
        lon, _ = VimsottariDasa()._seed_longitude(ch, "maandi")
        assert lon == pytest.approx(ch["planets"][Graha.MOON]["longitude"])


class TestAdMethods:
    def test_mahadasas_invariant_across_methods(self):
        cd, ch = _chart_dict()
        base = None
        for m in ["rao_rath", "raman", "continuous", "raghavacharya"]:
            periods = VimsottariDasa().compute(
                cd.julian_day, ch, DasaOptions(ad_method=m))
            mds = [(p.lord_name, round(p.duration_years, 6)) for p in periods]
            if base is None:
                base = mds
            else:
                assert mds == base

    def test_default_is_unchanged(self):
        cd, ch = _chart_dict()
        default = VimsottariDasa().compute(cd.julian_day, ch, DasaOptions())
        explicit = VimsottariDasa().compute(
            cd.julian_day, ch, DasaOptions(ad_method="rao_rath"))
        a = [(p.lord_name, p.start_jd) for p in default]
        b = [(p.lord_name, p.start_jd) for p in explicit]
        assert a == b

    def test_raman_halves_the_first_antardasa(self):
        cd, ch = _chart_dict()
        base = VimsottariDasa().compute(cd.julian_day, ch, DasaOptions())
        raman = VimsottariDasa().compute(
            cd.julian_day, ch, DasaOptions(ad_method="raman"))
        b0 = base[0].sub_periods[0]
        r0 = raman[0].sub_periods[0]
        assert r0.duration_years == pytest.approx(b0.duration_years / 2)

    def test_raghavacharya_changes_the_sub_order(self):
        cd, ch = _chart_dict()
        base = VimsottariDasa().compute(cd.julian_day, ch, DasaOptions())
        rv = VimsottariDasa().compute(
            cd.julian_day, ch, DasaOptions(ad_method="raghavacharya"))
        # The parent lord still opens the cycle, but the navamsa progression
        # steps the following sub-periods differently from the Vimsottari order.
        b_order = [s.lord_name for s in base[0].sub_periods]
        r_order = [s.lord_name for s in rv[0].sub_periods]
        assert b_order[0] == r_order[0]
        assert b_order != r_order


class TestNarayanaVariants:
    def test_default_matches_base(self):
        cd, ch = _chart_dict()
        a = NarayanaDasa().compute(cd.julian_day, ch, DasaOptions())
        b = NarayanaDasa().compute(
            cd.julian_day, ch, DasaOptions(narayana_variant="base"))
        assert [p.duration_years for p in a] == [p.duration_years for p in b]

    def test_sama_is_equal_ten_years(self):
        cd, ch = _chart_dict()
        p = NarayanaDasa().compute(
            cd.julian_day, ch, DasaOptions(narayana_variant="sama"))
        assert all(x.duration_years == pytest.approx(10.0) for x in p)

    def test_paka_doubles_the_seed(self):
        cd, ch = _chart_dict()
        base = NarayanaDasa().compute(cd.julian_day, ch, DasaOptions())
        paka = NarayanaDasa().compute(
            cd.julian_day, ch, DasaOptions(narayana_variant="paka"))
        assert (paka[0].duration_years
                == pytest.approx(base[0].duration_years * 2))


class TestPerVargaBhavaBala:
    def test_d1_unchanged(self):
        cd, _ch = _chart_dict()
        from jhora.calc.bhava_bala import BhavaBalaComputer
        a = BhavaBalaComputer(cd).compute_all()
        b = BhavaBalaComputer.for_varga(cd, "D_1").compute_all()
        assert a.results[1].total == b.results[1].total

    def test_varga_has_twelve_houses(self):
        cd, _ch = _chart_dict()
        from jhora.calc.bhava_bala import BhavaBalaComputer
        for lvl in ["D_9", "D_10", "D_60"]:
            r = BhavaBalaComputer.for_varga(cd, lvl).compute_all()
            assert len(r.results) == 12
            assert all(x.total > 0 for x in r.results.values())

    def test_varga_differs_from_rasi(self):
        cd, _ch = _chart_dict()
        from jhora.calc.bhava_bala import BhavaBalaComputer
        d1 = BhavaBalaComputer(cd).compute_all()
        d10 = BhavaBalaComputer.for_varga(cd, "D_10").compute_all()
        assert d1.results[10].total != d10.results[10].total


class TestDwadasaVargeeya:
    def test_scheme_has_twelve_vargas_summing_to_20(self):
        from jhora.calc.vimsopaka import VimsopakaScheme, _WEIGHTS
        w = _WEIGHTS[VimsopakaScheme.DWADASAVARGA]
        assert len(w) == 12
        assert sum(w.values()) == pytest.approx(20.0)

    def test_scores_in_range(self):
        cd, _ch = _chart_dict()
        from jhora.calc.vimsopaka import (
            VimsopakaComputer, VimsopakaScheme)
        for r in VimsopakaComputer(cd).compute_all(
                VimsopakaScheme.DWADASAVARGA):
            assert 0.0 <= r.total <= 20.0
