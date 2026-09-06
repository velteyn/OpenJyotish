"""Tests for Brahma Dasa computation (BPHS 'Sthira/Brahma dasa').

Faithful to the original jhora.exe (96-year cycle, movable/fixed/dual =
7/8/9 durations, first-mahadasa sesham) and to the extracted textbook
article (BPHS Brahma planet seed from stronger of lagna/7th).
"""

import pytest

from jhora.dasas.brahma import (
    BrahmaDasa, _brahma_planet, _rasi_lord, _planet_rasi,
)
from jhora.dasas.base import DasaOptions
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.dasa import PeriodLevel

# Reference chart (1970-04-04 23:18:20 IST, Chennai): sidereal Lahiri.
# Lagna = Sagittarius(8); Brahma planet = Mars (in Aries) → seed rasi Aries(0).
EXPECTED_SEED = Rasi.ARIES


def _chart_to_dict(ref_chart):
    return {
        "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                    for g, p in ref_chart.planets.items()},
        "lagna_lon": ref_chart.ascendant,
    }


@pytest.fixture
def engine():
    return BrahmaDasa()


class TestBrahmaHelpers:
    def test_rasi_lord(self):
        assert _rasi_lord(Rasi.ARIES) == Graha.MARS
        assert _rasi_lord(Rasi.PISCES) == Graha.JUPITER
        assert _rasi_lord(Rasi.AQUARIUS) == Graha.SATURN

    def test_seed_from_reference_chart(self, ref_chart):
        planets = {g: {"longitude": p.longitude}
                   for g, p in ref_chart.planets.items()}
        lagna_rasi = Rasi.from_longitude(ref_chart.ascendant)
        brahma = _brahma_planet(lagna_rasi, planets)
        assert brahma == Graha.MARS
        assert _planet_rasi(brahma, planets) == EXPECTED_SEED
class TestBrahmaCompute:
    def test_returns_12_mds(self, engine, ref_chart):
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        assert len(periods) == 12

    def test_starts_at_birth(self, engine, ref_chart):
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        assert abs(periods[0].start_jd - ref_chart.julian_day) < 0.01

    def test_seed_rasi_is_first_md(self, engine, ref_chart):
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        assert periods[0].lord_index == 100 + EXPECTED_SEED.value
        # Zodiacal sequence: Aries, Taurus, Gemini, ...
        second = Rasi((EXPECTED_SEED.value + 1) % 12)
        assert periods[1].lord_index == 100 + second.value

    def test_mds_sequential(self, engine, ref_chart):
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        for i in range(len(periods) - 1):
            assert abs(periods[i].end_jd - periods[i + 1].start_jd) < 0.01

    def test_durations_follow_7_8_9(self, engine, ref_chart):
        """Movable=7, fixed=8, dual=9 (108-year cycle)."""
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        # Skip the first reduced MD; check the full ones.
        expected = [None] + [_rasi_dur(Rasi((EXPECTED_SEED.value + i) % 12))
                             for i in range(1, 12)]
        for p, exp in zip(periods[1:], expected[1:]):
            assert abs(p.duration_years - exp) < 0.01

    def test_total_cycle_approx_96(self, engine, ref_chart):
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        total = sum(p.duration_years for p in periods)
        # Full cycle (7/8/9 over 12 signs) = 96 years. The first dasa is
        # reduced by the fraction of the seed sign remaining in Brahma's
        # longitude, so 96 - first_full < total < 96.
        first_full = _rasi_dur(EXPECTED_SEED)
        assert total < 96.0
        assert total > 96.0 - first_full

    def test_first_md_is_reduced(self, engine, ref_chart):
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        full_first = _rasi_dur(EXPECTED_SEED)
        assert periods[0].duration_years < full_first

    def test_antardasas_sum_to_md(self, engine, ref_chart):
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        for md in periods:
            if md.sub_periods:
                ad_sum = sum(ad.duration_years for ad in md.sub_periods)
                assert abs(ad_sum - md.duration_years) < 0.01

    def test_md_level(self, engine, ref_chart):
        periods = engine.compute(ref_chart.julian_day, _chart_to_dict(ref_chart))
        assert periods[0].level == PeriodLevel.MAHADASA


def _rasi_dur(rasi: Rasi) -> float:
    if rasi.is_movable:
        return 7.0
    if rasi.is_fixed:
        return 8.0
    return 9.0
