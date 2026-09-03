"""Tests for Vimsottari Dasa computation."""

import pytest

from jhora.dasas.vimsottari import VimsottariDasa
from jhora.dasas.base import DasaOptions
from jhora.types.graha import Graha
from jhora.types.dasa import DasaPeriod, PeriodLevel


@pytest.fixture
def dasa_engine():
    return VimsottariDasa()


class TestVimsottariConstants:
    def test_cycle_length(self):
        engine = VimsottariDasa()
        assert sum(engine.CYCLE_YEARS) == 120

    def test_lord_order(self):
        engine = VimsottariDasa()
        assert engine.CYCLE_LORDS[0] == Graha.KETU
        assert engine.CYCLE_LORDS[4] == Graha.MARS
        assert engine.CYCLE_LORDS[8] == Graha.MERCURY


class TestVimsottariCompute:
    """Test full dasa computation against reference chart."""

    def test_returns_9_mds(self, dasa_engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = dasa_engine.compute(ref_chart.julian_day, chart_dict)
        assert len(periods) == 9

    def test_first_md_starts_at_birth(self, dasa_engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = dasa_engine.compute(ref_chart.julian_day, chart_dict)
        assert abs(periods[0].start_jd - ref_chart.julian_day) < 0.01

    def test_mds_are_sequential(self, dasa_engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = dasa_engine.compute(ref_chart.julian_day, chart_dict)
        for i in range(len(periods) - 1):
            assert abs(periods[i].end_jd - periods[i + 1].start_jd) < 0.01

    def test_total_span(self, dasa_engine, ref_chart):
        """Total span should be 120 years minus the fraction remaining at birth."""
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = dasa_engine.compute(ref_chart.julian_day, chart_dict)
        first_dur = periods[0].duration_years
        remaining = sum(p.duration_years for p in periods)
        # First dasa is reduced by fraction remaining; total should be < 120
        assert remaining < 120.0
        assert remaining > 105.0

    def test_moon_nakshatra_determines_first_lord(self, dasa_engine, ref_chart):
        """First MD lord is the lord of Moon's nakshatra.
        
        Moon sidereal at 331.89° → Nakshatra 24 (Purva Bhadrapada) → Lord Jupiter
        Jupiter is at index 6 in the Vimsottari cycle (Ket=0, Ve=1, Su=2, Mo=3,
        Ma=4, Ra=5, Ju=6, Sa=7, Me=8).
        Graha.JUPITER.value = 4.
        """
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = dasa_engine.compute(ref_chart.julian_day, chart_dict)
        assert periods[0].lord_index == Graha.JUPITER.value

    def test_first_md_shorter_than_full(self, dasa_engine, ref_chart):
        """First MD is reduced because birth occurs mid-nakshatra."""
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = dasa_engine.compute(ref_chart.julian_day, chart_dict)
        mercury_full = Graha.MERCURY.vimsottari_years  # 17 years
        assert periods[0].duration_years < mercury_full
        assert periods[0].duration_years > 0


class TestVimsottariSubPeriods:
    def test_has_antardasas(self, dasa_engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = dasa_engine.compute(ref_chart.julian_day, chart_dict,
                                      DasaOptions(subdivision_level=PeriodLevel.ANTARDASA))
        assert periods[0].sub_periods is not None
        assert len(periods[0].sub_periods) == 9

    def test_ad_sum_matches_md(self, dasa_engine, ref_chart):
        """Sum of antardasa durations should equal mahadasa duration."""
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = dasa_engine.compute(ref_chart.julian_day, chart_dict,
                                      DasaOptions(subdivision_level=PeriodLevel.ANTARDASA))
        for md in periods:
            if md.sub_periods:
                ad_sum = sum(ad.duration_years for ad in md.sub_periods)
                assert abs(ad_sum - md.duration_years) < 0.01


class TestDasaBaseUtilities:
    def test_fraction_remaining(self):
        """At 0° progressed → 1.0 (whole life remaining)."""
        from jhora.dasas.base import DasaBase
        frac = DasaBase.compute_fraction_remaining(0.0, 13.333333)
        assert abs(frac - 1.0) < 0.001

    def test_fraction_half(self):
        from jhora.dasas.base import DasaBase
        frac = DasaBase.compute_fraction_remaining(6.666667, 13.333333)
        assert abs(frac - 0.5) < 0.001

    def test_fraction_near_end(self):
        from jhora.dasas.base import DasaBase
        frac = DasaBase.compute_fraction_remaining(13.0, 13.333333)
        assert frac < 0.1
        assert frac > 0.0

    def test_build_period_tree(self):
        from jhora.dasas.base import DasaBase
        lords = [(0, 6.0), (1, 10.0)]
        periods = DasaBase.build_period_tree(
            lords=lords,
            start_jd=2440000.0,
            cycle_total_years=120.0,
            sub_ratios=[6, 10, 7],
            y_per_d=365.2425,
            max_level=PeriodLevel.MAHADASA,
        )
        assert len(periods) == 2
        assert periods[0].lord_index == 0
        assert periods[1].lord_index == 1
        assert abs(periods[0].duration_years - 6.0) < 0.01

    def test_get_active_period(self):
        from jhora.dasas.base import DasaBase
        md = DasaPeriod(
            lord_index=0, lord_name="Ketu",
            start_jd=2440000.0, end_jd=2442556.0,
            duration_years=7.0,
        )
        active = DasaBase.get_active_period([md], 2441000.0)
        assert active is not None
        assert active.lord_name == "Ketu"

    def test_get_active_period_none(self):
        from jhora.dasas.base import DasaBase
        md = DasaPeriod(
            lord_index=0, lord_name="Ketu",
            start_jd=2440000.0, end_jd=2442556.0,
            duration_years=7.0,
        )
        active = DasaBase.get_active_period([md], 2443000.0)
        assert active is None


def _chart_dict(ref_chart) -> dict:
    return {
        "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                    for g, p in ref_chart.planets.items()},
        "lagna_lon": ref_chart.ascendant,
    }


class TestVimsottariSeedVariations:
    """The dasa seed determines which nakshatra (and thus first lord) starts."""

    def test_default_is_moon(self, ref_chart):
        engine = VimsottariDasa()
        opts = DasaOptions(start_variation="moon")
        periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
        # Moon at 1.89° Pisces → nakshatra 24 (Purva Bhadrapada) → lord Jupiter
        assert periods[0].lord_index == Graha.JUPITER.value

    def test_lagna_seed(self, ref_chart):
        engine = VimsottariDasa()
        opts = DasaOptions(start_variation="lagna")
        periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
        # Lagna at 241.26° → nakshatra 18 (Mula) → lord Ketu
        assert periods[0].lord_index == Graha.KETU.value

    def test_sun_seed(self, ref_chart):
        engine = VimsottariDasa()
        opts = DasaOptions(start_variation="sun")
        periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
        # Sun at 351.1° → nakshatra 26 (Revati) → lord Mercury
        assert periods[0].lord_index == Graha.MERCURY.value

    def test_different_seeds_give_different_first_lord(self, ref_chart):
        engine = VimsottariDasa()
        opts_moon = DasaOptions(start_variation="moon")
        opts_lagna = DasaOptions(start_variation="lagna")
        p_moon = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts_moon)
        p_lagna = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts_lagna)
        assert p_moon[0].lord_index != p_lagna[0].lord_index

    def test_tara_seeds_are_offsets_of_moon(self, ref_chart):
        from jhora.types.nakshatra import Nakshatra
        engine = VimsottariDasa()
        moon_lon = ref_chart.planet(Graha.MOON).longitude
        moon_nak, _ = Nakshatra.from_longitude(moon_lon)
        for variation, offset in [("kshema", 3), ("utpanna", 4), ("adhana", 7)]:
            opts = DasaOptions(start_variation=variation)
            periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
            seed_lord = periods[0].lord_index
            expected_lord = engine._nakshatra_to_graha(
                Nakshatra((moon_nak + offset) % 27)
            ).value
            assert seed_lord == expected_lord

    def test_invalid_variation_falls_back_to_moon(self, ref_chart):
        engine = VimsottariDasa()
        opts = DasaOptions(start_variation="not_a_seed")
        periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
        assert periods[0].lord_index == Graha.JUPITER.value


class TestVimsottariSesham:
    def test_full_sesham_gives_120_total(self, ref_chart):
        engine = VimsottariDasa()
        opts = DasaOptions(sesham_method="full")
        periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
        total = sum(p.duration_years for p in periods)
        assert abs(total - 120.0) < 0.01

    def test_moon_sesham_less_than_full(self, ref_chart):
        engine = VimsottariDasa()
        opts = DasaOptions(sesham_method="moon")
        periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
        total = sum(p.duration_years for p in periods)
        assert total < 120.0

    def test_full_first_md_not_reduced(self, ref_chart):
        engine = VimsottariDasa()
        opts = DasaOptions(sesham_method="full")
        periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
        first_lord = periods[0].lord_index
        openly = engine._cycle_years[Graha(first_lord)]
        assert abs(periods[0].duration_years - openly) < 0.01


class TestVimsottariYearDefinitions:
    def test_solar_vs_savana_durations(self, ref_chart):
        engine = VimsottariDasa()
        p_solar = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart),
                                 DasaOptions(year_definition="solar"))
        p_tithi = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart),
                                 DasaOptions(year_definition="tithi"))
        # Tithi year is shorter → same nominal years span fewer days → shorter
        assert p_solar[0].end_jd > p_tithi[0].end_jd

    def test_tithi_year_definition(self, ref_chart):
        engine = VimsottariDasa()
        opts = DasaOptions(year_definition="tithi", sesham_method="full")
        periods = engine.compute(ref_chart.julian_day, _chart_dict(ref_chart), opts)
        total = sum(p.duration_years for p in periods)
        assert abs(total - 120.0) < 0.01

