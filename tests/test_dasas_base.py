"""Tests for DasaBase — abstract base class for all dasa systems."""

import pytest

from jhora.dasas.base import DasaBase, DasaOptions, _subdivide
from jhora.types.dasa import DasaPeriod, PeriodLevel


class TestDasaOptions:
    def test_defaults(self):
        opts = DasaOptions()
        assert opts.year_definition == "solar"
        assert opts.start_variation == "moon"
        assert opts.subdivision_level == PeriodLevel.PRATYANTARDASA
        assert opts.include_subperiods is True
        assert opts.custom_sequence is None

    def test_custom(self):
        opts = DasaOptions(
            year_definition="savana",
            start_variation="lagna",
            subdivision_level=PeriodLevel.ANTARDASA,
            include_subperiods=False,
            custom_sequence=[1, 2, 3],
        )
        assert opts.year_definition == "savana"
        assert opts.subdivision_level == PeriodLevel.ANTARDASA
        assert opts.include_subperiods is False


class TestComputeFractionRemaining:
    def test_start_of_nakshatra(self):
        frac = DasaBase.compute_fraction_remaining(0.0, 13.333333)
        assert abs(frac - 1.0) < 0.001

    def test_end_of_nakshatra(self):
        frac = DasaBase.compute_fraction_remaining(13.333333, 13.333333)
        assert abs(frac - 0.0) < 0.001

    def test_mid_nakshatra(self):
        frac = DasaBase.compute_fraction_remaining(6.666667, 13.333333)
        assert abs(frac - 0.5) < 0.001

    def test_custom_span(self):
        frac = DasaBase.compute_fraction_remaining(5.0, 10.0)
        assert abs(frac - 0.5) < 0.001

    def test_range_zero_to_one(self):
        for deg in [0.0, 3.0, 7.0, 10.0, 13.0]:
            frac = DasaBase.compute_fraction_remaining(deg, 13.333333)
            assert 0.0 <= frac <= 1.0


class TestBuildPeriodTree:
    def test_simple_two_lords_no_subs(self):
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
        assert periods[0].sub_periods is None
        assert abs(periods[0].duration_years - 6.0) < 0.01
        assert abs(periods[1].duration_years - 10.0) < 0.01

    def test_sequential_mds(self):
        lords = [(0, 7.0), (1, 20.0), (2, 6.0)]
        periods = DasaBase.build_period_tree(
            lords=lords,
            start_jd=2440000.0,
            cycle_total_years=120.0,
            sub_ratios=[7, 20, 6, 10, 7, 18, 16, 19, 17],
            max_level=PeriodLevel.MAHADASA,
        )
        assert len(periods) == 3
        assert abs(periods[0].start_jd - 2440000.0) < 0.01
        assert abs(periods[0].end_jd - periods[1].start_jd) < 0.01
        assert abs(periods[1].end_jd - periods[2].start_jd) < 0.01

    def test_with_antardasas(self):
        lords = [(0, 7.0), (1, 20.0)]
        periods = DasaBase.build_period_tree(
            lords=lords,
            start_jd=2440000.0,
            cycle_total_years=120.0,
            sub_ratios=[7, 20, 6, 10, 7, 18, 16, 19, 17],
            max_level=PeriodLevel.ANTARDASA,
        )
        assert len(periods) == 2
        for md in periods:
            assert md.sub_periods is not None
            assert len(md.sub_periods) == 9  # one AD per lord in ratios
            for ad in md.sub_periods:
                assert ad.level == PeriodLevel.ANTARDASA
                assert ad.sub_periods is None  # no deeper subdivision

    def test_antardasa_durations_sum_to_md(self):
        lords = [(0, 7.0), (1, 20.0)]
        sub_ratios = [7, 20, 6, 10, 7, 18, 16, 19, 17]
        periods = DasaBase.build_period_tree(
            lords=lords,
            start_jd=2440000.0,
            cycle_total_years=120.0,
            sub_ratios=sub_ratios,
            max_level=PeriodLevel.ANTARDASA,
        )
        for md in periods:
            ad_sum = sum(ad.duration_years for ad in md.sub_periods)
            assert abs(ad_sum - md.duration_years) < 0.01

    def test_with_pratyantardasas(self):
        lords = [(0, 6.0)]
        periods = DasaBase.build_period_tree(
            lords=lords,
            start_jd=2440000.0,
            cycle_total_years=120.0,
            sub_ratios=[6, 10, 7],
            max_level=PeriodLevel.PRATYANTARDASA,
        )
        assert len(periods) == 1
        md = periods[0]
        assert md.sub_periods is not None
        assert len(md.sub_periods) == 3  # ADs
        for ad in md.sub_periods:
            assert ad.sub_periods is not None  # PDs exist
            assert len(ad.sub_periods) == 3
            for pd in ad.sub_periods:
                assert pd.level == PeriodLevel.PRATYANTARDASA
                assert pd.sub_periods is None

    def test_start_jd_offset(self):
        lords = [(0, 7.0)]
        start_jd = 2450000.0
        periods = DasaBase.build_period_tree(
            lords=lords,
            start_jd=start_jd,
            cycle_total_years=120.0,
            sub_ratios=[7],
            max_level=PeriodLevel.MAHADASA,
        )
        assert abs(periods[0].start_jd - start_jd) < 0.01

    def test_savana_year_definition(self):
        lords = [(0, 6.0)]
        periods = DasaBase.build_period_tree(
            lords=lords,
            start_jd=2440000.0,
            cycle_total_years=120.0,
            sub_ratios=[6],
            y_per_d=360.0,
            max_level=PeriodLevel.MAHADASA,
        )
        assert abs(periods[0].duration_years - 6.0) < 0.01
        assert abs((periods[0].end_jd - periods[0].start_jd) - (6.0 * 360.0)) < 0.01


class TestGetActivePeriod:
    def test_during_active_md(self):
        md = DasaPeriod(lord_index=0, lord_name="Ketu",
                        start_jd=2440000.0, end_jd=2442556.0,
                        duration_years=7.0)
        active = DasaBase.get_active_period([md], 2441000.0)
        assert active is not None
        assert active.lord_name == "Ketu"

    def test_before_period(self):
        md = DasaPeriod(lord_index=0, lord_name="Ketu",
                        start_jd=2440000.0, end_jd=2442556.0,
                        duration_years=7.0)
        active = DasaBase.get_active_period([md], 2430000.0)
        assert active is None

    def test_after_period(self):
        md = DasaPeriod(lord_index=0, lord_name="Ketu",
                        start_jd=2440000.0, end_jd=2442556.0,
                        duration_years=7.0)
        active = DasaBase.get_active_period([md], 2443000.0)
        assert active is None

    def test_at_exact_start(self):
        md = DasaPeriod(lord_index=0, lord_name="Ketu",
                        start_jd=2440000.0, end_jd=2442556.0,
                        duration_years=7.0)
        active = DasaBase.get_active_period([md], 2440000.0)
        assert active is not None

    def test_at_exact_end(self):
        """Exact end is not within [start, end) — should return None."""
        md = DasaPeriod(lord_index=0, lord_name="Ketu",
                        start_jd=2440000.0, end_jd=2442556.0,
                        duration_years=7.0)
        active = DasaBase.get_active_period([md], 2442556.0)
        assert active is None

    def test_during_second_md(self):
        md1 = DasaPeriod(lord_index=0, lord_name="Ketu",
                         start_jd=2440000.0, end_jd=2442000.0,
                         duration_years=5.0)
        md2 = DasaPeriod(lord_index=1, lord_name="Venus",
                         start_jd=2442000.0, end_jd=2444000.0,
                         duration_years=20.0)
        active = DasaBase.get_active_period([md1, md2], 2443000.0)
        assert active is not None
        assert active.lord_name == "Venus"

    def test_nested_subperiod(self):
        ad1 = DasaPeriod(lord_index=0, lord_name="Ketu-AD1",
                         start_jd=2440000.0, end_jd=2441000.0,
                         duration_years=2.74, level=PeriodLevel.ANTARDASA)
        ad2 = DasaPeriod(lord_index=1, lord_name="Venus-AD2",
                         start_jd=2441000.0, end_jd=2442556.0,
                         duration_years=4.26, level=PeriodLevel.ANTARDASA)
        md = DasaPeriod(lord_index=0, lord_name="Ketu",
                        start_jd=2440000.0, end_jd=2442556.0,
                        duration_years=7.0,
                        sub_periods=[ad1, ad2])
        active = DasaBase.get_active_period([md], 2441500.0)
        assert active is not None
        assert active.level == PeriodLevel.ANTARDASA
        assert active.lord_name == "Venus-AD2"

    def test_nested_pratyantardasa(self):
        pd = DasaPeriod(lord_index=2, lord_name="Sun-PD",
                        start_jd=2440500.0, end_jd=2441000.0,
                        duration_years=1.37, level=PeriodLevel.PRATYANTARDASA)
        ad = DasaPeriod(lord_index=0, lord_name="Ketu-AD",
                        start_jd=2440000.0, end_jd=2441000.0,
                        duration_years=2.74, level=PeriodLevel.ANTARDASA,
                        sub_periods=[pd])
        md = DasaPeriod(lord_index=0, lord_name="Ketu",
                        start_jd=2440000.0, end_jd=2442000.0,
                        duration_years=5.48,
                        sub_periods=[ad])
        active = DasaBase.get_active_period([md], 2440700.0)
        assert active is not None
        assert active.level == PeriodLevel.PRATYANTARDASA
        assert active.lord_name == "Sun-PD"

    def test_empty_list(self):
        active = DasaBase.get_active_period([], 2440000.0)
        assert active is None


class TestDasaBaseInstantiation:
    def test_default_options(self):
        """Cannot instantiate abstract class directly, but options are set."""
        class ConcreteDasa(DasaBase):
            system_name = "test"
            def compute(self, birth_jd, chart, options):
                return []
        d = ConcreteDasa()
        assert d.options is not None
        assert d.options.year_definition == "solar"

    def test_custom_options(self):
        opts = DasaOptions(year_definition="savana")
        class ConcreteDasa(DasaBase):
            system_name = "test"
            def compute(self, birth_jd, chart, options):
                return []
        d = ConcreteDasa(options=opts)
        assert d.options.year_definition == "savana"