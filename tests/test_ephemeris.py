"""Smoke tests for SweEngine and ChartBuilder (require Swiss Ephemeris)."""

import pytest

from jhora.ephemeris.swe import SweEngine, PlanetData
from jhora.charts.chart import ChartBuilder, ChartData


@pytest.fixture(scope="session")
def swe():
    return SweEngine()


class TestSweEngine:
    def test_julday_known(self, swe):
        """Julian day for a known date."""
        jd = swe.julday(1970, 1, 1, 0.0)
        assert abs(jd - 2440587.5) < 0.01

    def test_calc_sun(self, swe):
        """Sun position for a known date."""
        jd = swe.julday(1970, 4, 4, 17 + 48/60 + 20/3600)
        data = swe.calc_planet(0, jd)  # Sun
        assert isinstance(data, PlanetData)
        assert 0 <= data.longitude < 360
        assert isinstance(data.is_retrograde, bool)

    def test_calc_moon(self, swe):
        """Moon position for a known date."""
        jd = swe.julday(1970, 4, 4, 17.8056)
        data = swe.calc_planet(1, jd)  # Moon
        assert 0 <= data.longitude < 360

    def test_calc_all_planets(self, swe):
        """All 7 planets + nodes compute without error."""
        jd = swe.julday(1970, 4, 4, 17.8056)
        planets = swe.calc_planets(jd)
        assert len(planets) == 12  # 7 trad + 3 outer + Ra + Ke
        for pid, data in planets.items():
            assert 0 <= data.longitude < 360

    def test_houses(self, swe):
        """House cusps for Chennai."""
        jd = swe.julday(1970, 4, 4, 17.8056)
        hd = swe.houses(jd, 13.08, 80.27, b'P')
        assert len(hd.cusps) >= 12
        assert 0 <= hd.ascendant < 360
        assert 0 <= hd.mc < 360

    def test_revjul_roundtrip(self, swe):
        """Converting to JD and back gives the same date."""
        jd = swe.julday(1970, 4, 4, 12.0)
        y, m, d, h = swe.revjul(jd)
        assert y == 1970
        assert m == 4
        assert d == 4
        assert abs(h - 12.0) < 0.01

    def test_sidereal_mode_switch(self, swe):
        """Switching ayanamsa mode works."""
        orig = swe._ayanamsa_name
        swe.set_sidereal_mode("raman")
        assert swe._ayanamsa_name == "raman"
        swe.set_sidereal_mode("lahiri")
        assert swe._ayanamsa_name == "lahiri"


class TestChartBuilder:
    def test_build_reference(self):
        """Build reference chart and verify structure."""
        builder = ChartBuilder()
        cd = builder.build(
            year=1970, month=4, day=4,
            hour=17 + 48/60 + 20/3600,
            lat=13.08, lon=80.27,
            tz="+0530", ayanamsa="lahiri",
        )
        assert isinstance(cd, ChartData)
        assert cd.ascendant is not None
        assert len(cd.planets) == 9
        assert cd.lagna is not None
        assert len(cd.house_cusps) >= 12

    def test_build_different_ayanamsa(self):
        """Build with Raman ayanamsa produces different positions."""
        builder = ChartBuilder()
        cd_lahiri = builder.build(
            year=1970, month=4, day=4, hour=17.8056,
            lat=13.08, lon=80.27, tz="+0530", ayanamsa="lahiri",
        )
        cd_raman = builder.build(
            year=1970, month=4, day=4, hour=17.8056,
            lat=13.08, lon=80.27, tz="+0530", ayanamsa="raman",
        )
        # Longitudes should differ
        assert cd_lahiri.planets[0].longitude != cd_raman.planets[0].longitude

    def test_build_invalid_ayanamsa(self):
        """Unknown ayanamsa should raise ValueError."""
        builder = ChartBuilder()
        with pytest.raises(ValueError):
            builder.build(
                year=1970, month=4, day=4, hour=17.8056,
                lat=13.08, lon=80.27, tz="+0530", ayanamsa="nonexistent",
            )

    def test_build_retrograde_detection(self):
        """Retrograde status should be a boolean."""
        builder = ChartBuilder()
        cd = builder.build(
            year=1970, month=4, day=4, hour=17.8056,
            lat=13.08, lon=80.27, tz="+0530",
        )
        for g, p in cd.planets.items():
            assert isinstance(p.is_retrograde, bool)


class TestNodeMode:
    def test_mean_is_default(self):
        from jhora.ephemeris.swe import SweEngine
        assert SweEngine()._use_true_nodes is False

    def test_true_differs_within_bound(self):
        import swisseph as _swe
        from jhora.ephemeris.swe import SweEngine
        se = SweEngine()
        jd = se.julday(2001, 2, 24, 0.0)
        mean_lon = se.calc_planet(_swe.MEAN_NODE, jd).longitude
        se.set_use_true_nodes(True)
        true_lon = se.calc_planet(_swe.TRUE_NODE, jd).longitude
        delta = abs((true_lon - mean_lon + 180.0) % 360.0 - 180.0)
        assert 0.0 <= delta < 3.0

    def test_calc_planets_honors_mode(self):
        from jhora.ephemeris.swe import SweEngine
        se = SweEngine()
        jd = se.julday(2001, 2, 24, 0.0)
        mean_rahu = se.calc_planets(jd)[10].longitude
        se.set_use_true_nodes(True)
        out = se.calc_planets(jd)
        assert out[10].longitude != mean_rahu
        assert out[11].longitude == pytest.approx(
            (out[10].longitude + 180.0) % 360.0)
