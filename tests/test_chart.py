"""Tests for ChartBuilder, ChartData, and PlanetChartData."""

import pytest
from datetime import datetime

from jhora.charts.chart import ChartBuilder, ChartData, PlanetChartData, VargaPosition
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant
from jhora.ephemeris.swe import SweEngine
from conftest import REF_BIRTH, EXPECTED_RASI


class TestChartBuilder:
    def test_build_returns_chartdata(self):
        builder = ChartBuilder()
        cd = builder.build(**REF_BIRTH)
        assert isinstance(cd, ChartData)

    def test_build_all_nine_grahas(self, ref_chart):
        expected = {
            Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
            Graha.JUPITER, Graha.VENUS, Graha.SATURN,
            Graha.RAHU, Graha.KETU,
        }
        assert set(ref_chart.planets.keys()) == expected

    def test_lagna_computed(self, ref_chart):
        assert ref_chart.lagna is not None
        assert isinstance(ref_chart.lagna, PlanetChartData)
        assert ref_chart.lagna.dignity == "lagna"

    def test_ascendant_in_range(self, ref_chart):
        assert 0.0 <= ref_chart.ascendant < 360.0

    def test_sun_rasi_is_pisces(self, ref_chart):
        assert ref_chart.planets[Graha.SUN].rasi == Rasi.PISCES

    def test_moon_rasi_is_pisces(self, ref_chart):
        assert ref_chart.planets[Graha.MOON].rasi == Rasi.PISCES

    def test_mars_rasi_is_aries(self, ref_chart):
        assert ref_chart.planets[Graha.MARS].rasi == Rasi.ARIES

    def test_house_cusps_have_12_values(self, ref_chart):
        assert len(ref_chart.house_cusps) == 12

    def test_house_cusps_in_range(self, ref_chart):
        for cusp in ref_chart.house_cusps:
            assert 0.0 <= cusp < 360.0

    def test_julian_day_positive(self, ref_chart):
        assert ref_chart.julian_day > 2_440_000

    def test_every_planet_has_nakshatra(self, ref_chart):
        for g, p in ref_chart.planets.items():
            assert p.nakshatra is not None, f"{g} missing nakshatra"
            assert 1 <= p.nakshatra_pada <= 4, f"{g} pada out of range"

    def test_rahu_and_ketu_have_node_dignity(self, ref_chart):
        assert ref_chart.planets[Graha.RAHU].dignity == "node"
        assert ref_chart.planets[Graha.KETU].dignity == "node"

    def test_dignity_computed_for_all(self, ref_chart):
        for g, p in ref_chart.planets.items():
            assert p.dignity, f"{g} missing dignity"
            assert isinstance(p.dignity, str)

    def test_birth_date_stored(self, ref_chart):
        assert ref_chart.birth_date == datetime(1970, 4, 4)

    def test_ayanamsa_stored(self, ref_chart):
        assert ref_chart.ayanamsa_name == "lahiri"
        assert ref_chart.ayanamsa_value > 0

    def test_all_longitudes_in_range(self, ref_chart):
        for p in ref_chart.planets.values():
            assert 0.0 <= p.longitude < 360.0

    def test_degrees_in_rasi_range(self, ref_chart):
        for p in ref_chart.planets.values():
            assert 0.0 <= p.degrees_in_rasi < 30.0

    def test_planet_speed_present(self, ref_chart):
        for p in ref_chart.planets.values():
            assert isinstance(p.speed, (int, float))

    def test_sidereal_flag_is_applied(self):
        """Bugfix: set_sidereal_mode must be called so results are sidereal.
        
        Tropical Sun on 1970-04-04 ~17:48 UT would be ~14.5° Aries.
        Sidereal Lahiri subtracts ~23.5°, giving ~21° Pisces (~351°).
        """
        builder = ChartBuilder()
        cd = builder.build(**REF_BIRTH)
        sun_lon = cd.sun.longitude
        assert sun_lon > 340 and sun_lon < 360, (
            f"Sun at {sun_lon:.1f}° — expected sidereal position near 351°, not tropical 14°"
        )
        assert cd.sun.rasi == Rasi.PISCES, (
            f"Sun in {cd.sun.rasi_name}, expected Pisces (sidereal)"
        )
        assert cd.ayanamsa_value > 20.0, "Ayanamsa should be ~23.5° for 1970"

    def test_different_ayanamsa_different_result(self):
        """Raman ayanamsa produces different planet longitudes than Lahiri."""
        b1 = ChartBuilder()
        cd1 = b1.build(year=1970, month=4, day=4, hour=17.81,
                       lat=13.08, lon=80.27, tz="+0530", ayanamsa="lahiri")
        b2 = ChartBuilder()
        cd2 = b2.build(year=1970, month=4, day=4, hour=17.81,
                       lat=13.08, lon=80.27, tz="+0530", ayanamsa="raman")
        assert abs(cd1.sun.longitude - cd2.sun.longitude) > 0.5, (
            f"Different ayanamsas should produce different longitudes: "
            f"Lahiri={cd1.sun.longitude:.4f}, Raman={cd2.sun.longitude:.4f}"
        )

    def test_build_with_custom_ayanamsa(self):
        builder = ChartBuilder()
        cd = builder.build(year=1970, month=4, day=4, hour=12.0,
                           lat=13.08, lon=80.27, tz="+0530",
                           ayanamsa="raman")
        assert cd.ayanamsa_name == "raman"

    def test_build_with_custom_house_system(self):
        builder = ChartBuilder()
        cd = builder.build(year=1970, month=4, day=4, hour=12.0,
                           lat=13.08, lon=80.27, tz="+0530",
                           house_sys=b'K')
        assert len(cd.house_cusps) == 12

    def test_longitudes_match_expected_approx(self, ref_chart):
        for g, (exp_rasi, exp_deg, _dignity) in EXPECTED_RASI.items():
            if g not in ref_chart.planets:
                continue
            p = ref_chart.planets[g]
            approx_deg = abs(p.degrees_in_rasi - exp_deg) < 1.5
            assert approx_deg, (
                f"{g.full_name}: expected ~{exp_deg}° in {exp_rasi}, "
                f"got {p.degrees_in_rasi:.2f}° in {p.rasi_name}"
            )

    def test_retrograde_flag_is_bool(self, ref_chart):
        for p in ref_chart.planets.values():
            assert isinstance(p.is_retrograde, bool)


class TestChartData:
    def test_planet_method(self, ref_chart):
        sun = ref_chart.planet(Graha.SUN)
        assert isinstance(sun, PlanetChartData)
        assert sun.graha == Graha.SUN

    def test_sun_property(self, ref_chart):
        assert ref_chart.sun.graha == Graha.SUN

    def test_moon_property(self, ref_chart):
        assert ref_chart.moon.graha == Graha.MOON

    def test_varga_positions_default_empty(self, ref_chart):
        assert ref_chart.varga_positions == {}

    def test_frozen_dataclass(self, ref_chart):
        with pytest.raises(Exception):
            ref_chart.ayanamsa_name = "raman"  # type: ignore


class TestPlanetChartData:
    def test_rasi_name_property(self, ref_chart):
        sn = ref_chart.sun
        assert isinstance(sn.rasi_name, str)
        assert len(sn.rasi_name) > 2

    def test_nakshatra_name_property(self, ref_chart):
        sn = ref_chart.sun
        assert isinstance(sn.nakshatra_name, str)
        assert len(sn.nakshatra_name) > 2

    def test_speed_float(self, ref_chart):
        for p in ref_chart.planets.values():
            assert isinstance(p.speed, (int, float))

    def test_latitude_is_present(self, ref_chart):
        for p in ref_chart.planets.values():
            assert isinstance(p.latitude, (int, float))


class TestChartBuilderCustomInput:
    def test_build_far_future(self):
        builder = ChartBuilder()
        cd = builder.build(year=2099, month=1, day=1, hour=12.0,
                           lat=28.61, lon=77.23, tz="+0530")
        assert isinstance(cd, ChartData)
        assert cd.birth_date == datetime(2099, 1, 1)

    def test_build_southern_hemisphere(self):
        builder = ChartBuilder()
        cd = builder.build(year=1980, month=6, day=15, hour=6.0,
                           lat=-33.87, lon=151.21, tz="+1000")
        assert isinstance(cd, ChartData)
        assert cd.latitude == -33.87
        assert 0.0 <= cd.ascendant < 360.0

    def test_build_midnight_birth(self):
        builder = ChartBuilder()
        cd = builder.build(year=2000, month=1, day=1, hour=0.0,
                           lat=40.71, lon=-74.01, tz="-0500")
        assert isinstance(cd, ChartData)

    def test_build_twice_with_same_input_yields_consistent(self):
        builder1 = ChartBuilder()
        builder2 = ChartBuilder()
        cd1 = builder1.build(**REF_BIRTH)
        cd2 = builder2.build(**REF_BIRTH)
        assert cd1.ascendant == cd2.ascendant
        assert cd1.julian_day == cd2.julian_day

    def test_ayanamsa_actual_value_nonzero(self, ref_chart):
        assert ref_chart.ayanamsa_value > 20.0
        assert ref_chart.ayanamsa_value < 26.0


class TestVargaPosition:
    def test_creation(self):
        vp = VargaPosition(
            graha=Graha.MOON, varga_level=VargaLevel.D_9,
            variant=VargaVariant.DEFAULT, longitude=45.0,
            rasi=Rasi.TAURUS, degrees_in_rasi=15.0,
        )
        assert vp.graha == Graha.MOON
        assert vp.varga_level == VargaLevel.D_9
        assert vp.rasi == Rasi.TAURUS