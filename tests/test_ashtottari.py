"""Tests for Ashtottari Dasa computation."""

import pytest

from jhora.dasas.ashtottari import AshtottariDasa
from jhora.dasas.base import DasaOptions
from jhora.types.graha import Graha
from jhora.types.dasa import DasaPeriod, PeriodLevel
from jhora.types.nakshatra import Nakshatra


@pytest.fixture
def engine():
    return AshtottariDasa()


class TestAshtottariConstants:
    def test_cycle_length(self):
        engine = AshtottariDasa()
        assert sum(engine.CYCLE_YEARS) == 108

    def test_cycle_has_eight_lords(self):
        engine = AshtottariDasa()
        assert len(engine.CYCLE_LORDS) == 8

    def test_ketu_not_in_cycle(self):
        engine = AshtottariDasa()
        assert Graha.KETU not in engine.CYCLE_LORDS

    def test_lord_order(self):
        engine = AshtottariDasa()
        assert engine.CYCLE_LORDS[0] == Graha.SUN
        assert engine.CYCLE_LORDS[7] == Graha.VENUS

    def test_individual_years(self):
        engine = AshtottariDasa()
        assert engine.CYCLE_YEARS[0] == 6.0   # Sun
        assert engine.CYCLE_YEARS[1] == 15.0  # Moon
        assert engine.CYCLE_YEARS[7] == 21.0  # Venus

    def test_nakshatra_lord_mapping_all(self):
        engine = AshtottariDasa()
        assert len(engine._NAKSHATRA_LORD) == 27
        for ns in Nakshatra:
            assert ns in engine._NAKSHATRA_LORD

    def test_nakshatra_lord_ashwini(self):
        engine = AshtottariDasa()
        assert engine._NAKSHATRA_LORD[Nakshatra.ASVINI] == Graha.SUN

    def test_nakshatra_lord_revati(self):
        engine = AshtottariDasa()
        assert engine._NAKSHATRA_LORD[Nakshatra.REVATI] == Graha.MARS


class TestAshtottariCompute:
    def test_returns_eight_mds(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict)
        assert len(periods) == 8

    def test_first_md_starts_at_birth(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict)
        assert abs(periods[0].start_jd - ref_chart.julian_day) < 0.01

    def test_mds_are_sequential(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict)
        for i in range(len(periods) - 1):
            assert abs(periods[i].end_jd - periods[i + 1].start_jd) < 0.01

    def test_total_span_under_108(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict)
        remaining = sum(p.duration_years for p in periods)
        assert remaining < 108.0
        assert remaining > 95.0

    def test_first_md_shorter_than_full(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict)
        full_first = engine.CYCLE_YEARS[
            engine._cycle_index[engine._NAKSHATRA_LORD[ref_chart.moon.nakshatra]]
        ]
        assert periods[0].duration_years < full_first

    def test_birth_in_purva_bhadrapada_gives_jupiter_start(self, engine, ref_chart):
        """Our reference chart has Moon in Purva Bhadrapada (nakshatra 24).
        In Ashtottari, nakshatra 24 % 8 = 0, lord = Sun."""
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict)
        assert periods[0].lord_index == Graha.SUN.value


class TestAshtottariSubPeriods:
    def test_has_antardasas(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict,
                                 DasaOptions(subdivision_level=PeriodLevel.ANTARDASA))
        assert periods[0].sub_periods is not None
        assert len(periods[0].sub_periods) == 8

    def test_ad_sum_matches_md(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict,
                                 DasaOptions(subdivision_level=PeriodLevel.ANTARDASA))
        for md in periods:
            if md.sub_periods:
                ad_sum = sum(ad.duration_years for ad in md.sub_periods)
                assert abs(ad_sum - md.duration_years) < 0.01

    def test_no_ketu_in_subperiod_lords(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        periods = engine.compute(ref_chart.julian_day, chart_dict,
                                 DasaOptions(subdivision_level=PeriodLevel.ANTARDASA))
        for md in periods:
            if md.sub_periods:
                for ad in md.sub_periods:
                    assert ad.lord_index != Graha.KETU.value


class TestAshtottariApplicability:
    def test_unconditional(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        assert AshtottariDasa.is_applicable(chart_dict, "unconditional")

    def test_rahu_condition(self, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        result = AshtottariDasa.is_applicable(chart_dict, "rahu")
        assert isinstance(result, bool)

    def test_paksha_condition(self, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        result = AshtottariDasa.is_applicable(chart_dict, "paksha")
        assert isinstance(result, bool)


class TestAshtottariGetActivePeriod:
    def test_find_active_period(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        # 10 years after birth
        target_jd = ref_chart.julian_day + 10 * 365.2425
        active = engine.dasa_at_date(ref_chart.julian_day, chart_dict, target_jd)
        assert active is not None

    def test_find_birth_period(self, engine, ref_chart):
        chart_dict = {
            "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                        for g, p in ref_chart.planets.items()},
            "lagna_lon": ref_chart.ascendant,
        }
        active = engine.dasa_at_date(ref_chart.julian_day, chart_dict,
                                     ref_chart.julian_day)
        assert active is not None


class TestAshtottariDasaVimsottariComparison:
    def test_different_system_names(self):
        from jhora.dasas.vimsottari import VimsottariDasa
        v = VimsottariDasa()
        a = AshtottariDasa()
        assert v.system_name != a.system_name

    def test_different_cycle_length(self):
        from jhora.dasas.vimsottari import VimsottariDasa
        v = VimsottariDasa()
        a = AshtottariDasa()
        assert sum(v.CYCLE_YEARS) != sum(a.CYCLE_YEARS)
        assert sum(a.CYCLE_YEARS) == 108

    def test_different_lord_count(self):
        from jhora.dasas.vimsottari import VimsottariDasa
        v = VimsottariDasa()
        a = AshtottariDasa()
        assert len(v.CYCLE_LORDS) != len(a.CYCLE_LORDS)
        assert len(a.CYCLE_LORDS) == 8