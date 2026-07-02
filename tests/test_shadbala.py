"""Tests for Shadbala — six-fold planetary strength computation."""

import pytest
from jhora.calc.shadbala import (
    ShadbalaComputer, ShadbalaComponent, ShadbalaResult,
    _RUPA, _NAISARGIKA_BALA, _DIG_BALA_HOUSE,
)
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha


@pytest.fixture(scope="module")
def chart():
    builder = ChartBuilder()
    return builder.build(1990, 1, 15, 12.0, 12.9716, 77.5946, tz="Asia/Kolkata")


@pytest.fixture(scope="module")
def shadbala(chart):
    return ShadbalaComputer(chart)


@pytest.fixture(scope="module")
def results(shadbala):
    return shadbala.compute()


class TestShadbalaResult:
    def test_all_planets_present(self, results):
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                   Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            assert g in results

    def test_result_type(self, results):
        for r in results.values():
            assert isinstance(r, ShadbalaResult)
            assert isinstance(r.sthana, dict)
            assert isinstance(r.dig, dict)
            assert isinstance(r.kala, dict)
            assert isinstance(r.chesta, dict)
            assert isinstance(r.naisargika, ShadbalaComponent)
            assert isinstance(r.drik, ShadbalaComponent)

    def test_total_properties(self, results):
        for r in results.values():
            assert r.total_virupa > 0
            assert r.total_rupa > 0
            assert r.total_rupa == pytest.approx(r.total_virupa / 60.0)
            assert r.sthana_total >= 0
            assert r.dig_total >= 0
            assert r.kala_total >= 0
            assert r.chesta_total >= 0

    def test_summary_string(self, results):
        for r in results.values():
            s = r.summary()
            assert r.graha.full_name in s
            assert "Tot=" in s


class TestSthanaBala:
    def test_uchcha_bala_range(self, results):
        for r in results.values():
            uchcha = r.sthana["uchcha"]
            assert 0 <= uchcha.virupa <= 60
            assert uchcha.max_virupa == 60

    def test_uchcha_bala_strong_exalted(self, chart):
        builder = ChartBuilder()
        cd = builder.build(2000, 9, 15, 6.0, 28.6, 77.2, tz="Asia/Kolkata")
        comp = ShadbalaComputer(cd)
        res = comp.compute_one(Graha.SATURN)
        assert res.sthana["uchcha"].virupa > 0

    def test_saptavargaja_bala_range(self, results):
        for r in results.values():
            sv = r.sthana["saptavargaja"]
            assert 0 <= sv.virupa <= 315
            assert sv.max_virupa == 315

    def test_ojhayugma_bala_range(self, results):
        for r in results.values():
            oj = r.sthana["ojhayugma"]
            assert oj.virupa in (0, 15)
            assert oj.max_virupa == 15

    def test_ojhayugma_mercury_always(self, chart):
        comp = ShadbalaComputer(chart)
        r = comp.compute_one(Graha.MERCURY)
        assert r.sthana["ojhayugma"].virupa == 15

    def test_kendra_bala_range(self, results):
        for r in results.values():
            kendra = r.sthana["kendra"]
            assert kendra.virupa in (15, 30, 60)
            assert kendra.max_virupa == 60

    def test_drekkana_bala_range(self, results):
        for r in results.values():
            dr = r.sthana["drekkana"]
            assert dr.virupa in (0, 15)
            assert dr.max_virupa == 15


class TestDigBala:
    def test_dig_bala_range(self, results):
        for r in results.values():
            dig = r.dig.get("dig")
            if dig:
                assert 0 <= dig.virupa <= 60
                assert dig.max_virupa == 60

    def test_sun_dig_bala_10th_house(self):
        builder = ChartBuilder()
        cd = builder.build(2000, 3, 21, 6.0, 0.0, 0.0, tz="UTC")
        comp = ShadbalaComputer(cd)
        r = comp.compute_one(Graha.SUN)
        assert r.dig["dig"].virupa >= 0


class TestKalaBala:
    def test_nathonnatha_bala_range(self, results):
        for r in results.values():
            nn = r.kala["nathonnatha"]
            assert 0 <= nn.virupa <= 60
            assert nn.max_virupa == 60

    def test_paksha_bala_range(self, results):
        for r in results.values():
            pk = r.kala["paksha"]
            assert pk.virupa in (0, 60)
            assert pk.max_virupa == 60

    def test_tribhaga_bala_range(self, results):
        for r in results.values():
            tb = r.kala["tribhaga"]
            assert tb.virupa in (0, 60)
            assert tb.max_virupa == 60

    def test_abda_bala_range(self, results):
        for r in results.values():
            ab = r.kala["abda"]
            assert ab.virupa in (0, 15)
            assert ab.max_virupa == 15

    def test_masa_bala_range(self, results):
        for r in results.values():
            ms = r.kala["masa"]
            assert ms.virupa in (0, 30)
            assert ms.max_virupa == 30

    def test_vara_bala_range(self, results):
        for r in results.values():
            vr = r.kala["vara"]
            assert vr.virupa in (0, 45)
            assert vr.max_virupa == 45

    def test_hora_bala_range(self, results):
        for r in results.values():
            hr = r.kala["hora"]
            assert hr.virupa in (0, 60)
            assert hr.max_virupa == 60

    def test_ayana_bala_range(self, results):
        for r in results.values():
            ay = r.kala["ayana"]
            assert 0 <= ay.virupa <= 60
            assert ay.max_virupa == 60

    def test_abda_bala_exactly_one_lord(self, results):
        abda_max = sum(1 for r in results.values() if r.kala["abda"].virupa == 15)
        assert abda_max == 1

    def test_vara_bala_exactly_one_lord(self, results):
        vara_max = sum(1 for r in results.values() if r.kala["vara"].virupa == 45)
        assert vara_max == 1

    def test_masa_bala_exactly_one_lord(self, results):
        masa_max = sum(1 for r in results.values() if r.kala["masa"].virupa == 30)
        assert masa_max == 1


class TestChestaBala:
    def test_chesta_bala_range(self, results):
        for r in results.values():
            if r.kala.get("chesta"):
                c = r.chesta["chesta"]
                assert 0 <= c.virupa <= 60

    def test_sun_moon_chesta_fixed(self, results):
        for g in (Graha.SUN, Graha.MOON):
            r = results[g]
            c = r.chesta["chesta"]
            assert c.virupa > 0
            assert c.max_virupa == 60


class TestNaisargikaBala:
    def test_naisargika_values(self, results):
        for g, r in results.items():
            expected = _NAISARGIKA_BALA.get(g, 0)
            assert r.naisargika.virupa == pytest.approx(expected, abs=0.1)
            assert r.naisargika.max_virupa == pytest.approx(expected, abs=0.1)

    def test_sun_naisargika_highest(self):
        assert _NAISARGIKA_BALA[Graha.SUN] == 60.0


class TestDrikBala:
    def test_drik_bala_range(self, results):
        for r in results.values():
            assert 0 <= r.drik.virupa <= 60
            assert r.drik.max_virupa == 60


class TestShadbalaComponent:
    def test_rupa_conversion(self):
        c = ShadbalaComponent("test", 30, 60)
        assert c.rupa == 0.5
        assert c.pct == 50.0

    def test_pct_zero_max(self):
        c = ShadbalaComponent("test", 10, 0)
        assert c.pct == 0.0


class TestComputeOne:
    def test_compute_one_matches_compute(self, shadbala):
        full = shadbala.compute()
        for g in [Graha.SUN, Graha.MOON, Graha.MARS]:
            one = shadbala.compute_one(g)
            full_r = full[g]
            assert one.total_virupa == pytest.approx(full_r.total_virupa)


class TestTotalRanges:
    def test_total_rupa_positive(self, results):
        for r in results.values():
            assert r.total_rupa > 0

    def test_total_rupa_reasonable(self, results):
        for r in results.values():
            assert 1.0 <= r.total_rupa <= 20.0

    def test_strongest_planet_reasonable(self, results):
        strongest = max(results.values(), key=lambda r: r.total_virupa)
        assert strongest.graha in [Graha.SUN, Graha.MOON, Graha.MARS,
                                     Graha.MERCURY, Graha.JUPITER,
                                     Graha.VENUS, Graha.SATURN]