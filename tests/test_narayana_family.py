"""Lagnamsaka and Padanaathaamsa — Narayana-family seed variants."""

from jhora.calc.arudha import bhava_arudha
from jhora.calc.jaimini_strength import chart_signs_lons, stronger_rasi
from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.narayana import NarayanaDasa, _LORD_NAME_TO_GRAHA
from jhora.dasas.narayana_variants import LagnamsakaDasa, PadanaathaamsaDasa
from jhora.types.rasi import Rasi


def _chart():
    cd = ChartBuilder().build(1990, 1, 15, 17.5, 12.9716, 77.5946, tz="+0530")
    d = {"planets": {g: {"longitude": p.longitude}
                     for g, p in cd.planets.items()},
         "lagna_lon": cd.ascendant}
    return cd, d


class TestNarayanaSequence:
    def test_sequence_visits_all_twelve_signs(self):
        for seed in range(12):
            seq = NarayanaDasa._compute_sequence(Rasi(seed))
            assert len(seq) == 12
            assert len({r.value for r in seq}) == 12

    def test_direction_from_the_ninth_sign_foot(self):
        # seed Aries → 9th is Sagittarius (even index) → forward
        assert [r.value for r in NarayanaDasa._compute_sequence(Rasi(0))] == \
            list(range(12))
        # seed Taurus → 9th is Capricorn (odd index) → backward
        assert [r.value for r in NarayanaDasa._compute_sequence(Rasi(1))] == \
            [1, 0, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]


class TestNarayanaFamily:
    def test_lagnamsaka_seeds_from_stronger_of_lagna_and_seventh(self):
        cd, d = _chart()
        lagna = Rasi.from_longitude(d["lagna_lon"])
        signs, lons = chart_signs_lons(d)
        seed = Rasi(stronger_rasi(lagna.value, (lagna.value + 6) % 12,
                                  signs, lons))
        periods = LagnamsakaDasa().compute(cd.julian_day, d, DasaOptions())
        assert len(periods) == 12
        assert periods[0].lord_name == seed.full_name

    def test_lagnamsaka_uses_the_narayana_progression(self):
        cd, d = _chart()
        lagna = Rasi.from_longitude(d["lagna_lon"])
        signs, lons = chart_signs_lons(d)
        seed = Rasi(stronger_rasi(lagna.value, (lagna.value + 6) % 12,
                                  signs, lons))
        expected = [r.value for r in NarayanaDasa._compute_sequence(seed)]
        got = [p.lord_index - 100 for p in
               LagnamsakaDasa().compute(cd.julian_day, d, DasaOptions())]
        assert got == expected

    def test_padanaathaamsa_seeds_from_al_lord_sign(self):
        cd, d = _chart()
        al = bhava_arudha(1, d["lagna_lon"], d["planets"])
        lord = _LORD_NAME_TO_GRAHA[al.lord]
        seed = Rasi.from_longitude(d["planets"][lord]["longitude"])
        periods = PadanaathaamsaDasa().compute(cd.julian_day, d, DasaOptions())
        assert periods[0].lord_name == seed.full_name

    def test_variants_have_twelve_distinct_positive_periods(self):
        cd, d = _chart()
        for engine in (LagnamsakaDasa(), PadanaathaamsaDasa()):
            periods = engine.compute(cd.julian_day, d, DasaOptions())
            assert len(periods) == 12
            assert len({p.lord_index for p in periods}) == 12
            assert all(p.duration_years > 0 for p in periods)
