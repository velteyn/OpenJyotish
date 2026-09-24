"""Tests for Tajaka yogas (PVR ch. 29.2 worked numbers as gold)."""

from jhora.calc.tajaka_yoga import (
    _house_yogas, approaching, aspect_kind, deeptamsa_check, eesarpha,
    ithasala,
)
from jhora.types.graha import Graha

# Typical direct speeds (°/day).
V = {Graha.SUN: 1.0, Graha.MOON: 13.2, Graha.MARS: 0.5,
     Graha.MERCURY: 1.5, Graha.JUPITER: 0.1, Graha.VENUS: 1.2,
     Graha.SATURN: 0.06}


def LE(deg):
    return 120.0 + deg


def LI(deg):
    return 180.0 + deg


class TestAspects:
    def test_sextile_trine_square_etc(self):
        assert aspect_kind(4, 6) == "benefic"  # Le → Li sextile
        assert aspect_kind(2, 6) == "benefic"  # Ge → Li trine
        assert aspect_kind(0, 0) == "malefic"  # conjunction
        assert aspect_kind(0, 6) == "malefic"  # opposition
        assert aspect_kind(0, 3) == "malefic"  # square
        assert aspect_kind(0, 1) == "neutral"  # semi-sextile
        assert aspect_kind(0, 5) is None  # 6th apart: no aspect
        assert aspect_kind(2, 7) is None  # Ge → Sc: none


class TestIthasalaGold:
    def test_vartamaana(self):
        # Moon 14Le / Venus 19Li sextile, mutual orb.
        assert ithasala(LE(14), LI(19), V[Graha.MOON], V[Graha.VENUS],
                        Graha.MOON, Graha.VENUS) == "Vartamaana"

    def test_poorna(self):
        # Moon 18°25'Le: advancements within 1°.
        assert ithasala(LE(18 + 25 / 60), LI(19), V[Graha.MOON],
                        V[Graha.VENUS],
                        Graha.MOON, Graha.VENUS) == "Poorna"

    def test_bhavishya(self):
        # Moon 13°35'Le / Venus 21°20'Li: Moon 0.75° short of Venus's orb.
        assert ithasala(LE(13 + 35 / 60), LI(21 + 20 / 60),
                        V[Graha.MOON], V[Graha.VENUS],
                        Graha.MOON, Graha.VENUS) == "Bhavishya"

    def test_retrograde_faster_behind_is_no_ithasala(self):
        # Mercury 18Ge retro / Mars 18°10'Li: separating despite proximity.
        assert ithasala(60 + 18, 180 + 18 + 10 / 60, -0.5, V[Graha.MARS],
                        Graha.MERCURY, Graha.MARS) is None
        assert eesarpha(60 + 18, 180 + 18 + 10 / 60, -0.5,
                        V[Graha.MARS],
                        Graha.MERCURY, Graha.MARS) is True

    def test_retrograde_faster_ahead_is_ithasala(self):
        # Mars 21Cp / Mercury 23Vi retro: moving toward each other.
        assert ithasala(270 + 21, 150 + 23, V[Graha.MARS], -0.5,
                        Graha.MARS, Graha.MERCURY) == "Vartamaana"


class TestEesarphaGold:
    def test_separating(self):
        # Moon 23Le / Venus 19Li: faster more advanced.
        assert ithasala(LE(23), LI(19), V[Graha.MOON], V[Graha.VENUS],
                        Graha.MOON, Graha.VENUS) is None
        assert eesarpha(LE(23), LI(19), V[Graha.MOON], V[Graha.VENUS],
                        Graha.MOON, Graha.VENUS) is True


class TestHouses:
    def test_ishkavala(self):
        assert _house_yogas({1, 2, 4, 5, 7, 8, 10, 11}) == (True, False)

    def test_induvara(self):
        assert _house_yogas({3, 6, 9, 12}) == (False, True)

    def test_mixed(self):
        assert _house_yogas({1, 3}) == (False, False)
        assert _house_yogas(set()) == (False, False)


def _syn_chart(lons, speeds=None, lagna=30.0):
    """Synthetic ChartData-like stub with chosen longitudes/speeds."""
    from jhora.charts.chart import PlanetChartData
    from jhora.types.nakshatra import Nakshatra
    from jhora.types.rasi import Rasi
    speeds = speeds or {}
    planets = {}
    for g, lon in lons.items():
        planets[g] = PlanetChartData(
            graha=g, longitude=lon, latitude=0.0,
            speed=speeds.get(g, V.get(g, 0.5)),
            is_retrograde=speeds.get(g, 1.0) < 0,
            rasi=Rasi(int(lon // 30) % 12),
            degrees_in_rasi=lon % 30,
            nakshatra=Nakshatra.from_longitude(lon)[0],
            nakshatra_pada=1, dignity="normal",
        )

    class Stub:
        def planet(self, graha):
            return self.planets[graha]
    stub = Stub()
    stub.ascendant = lagna
    stub.planets = planets
    return stub


class TestTriplesGold:
    def test_nakta_example(self):
        # Lagna Ta; Venus 13Ge, Mars 15Sc (no aspect); Moon 11Cn
        # in ithasala with both → Nakta(Venus, Mars, Moon).
        from jhora.calc.tajaka_yoga import tajaka_yogas
        cd = _syn_chart({Graha.SUN: 0.0, Graha.MOON: 101.0,
                         Graha.MARS: 225.0, Graha.MERCURY: 0.0,
                         Graha.JUPITER: 0.0, Graha.VENUS: 73.0,
                         Graha.SATURN: 0.0}, lagna=30.0)
        out = tajaka_yogas(cd)
        assert (Graha.MARS, Graha.VENUS, Graha.MOON) in out.naktas

    def test_khallasara_example(self):
        # Lagna Vi; Moon 1Ar, Mercury 15Ta, Jupiter 29Ge.
        from jhora.calc.tajaka_yoga import tajaka_yogas
        cd = _syn_chart({Graha.SUN: 0.0, Graha.MOON: 1.0,
                         Graha.MARS: 300.0, Graha.MERCURY: 45.0,
                         Graha.JUPITER: 89.0, Graha.VENUS: 300.0,
                         Graha.SATURN: 300.0}, lagna=150.0)
        out = tajaka_yogas(cd)
        assert (Graha.MERCURY, Graha.JUPITER) in out.khallasaras

    def test_manahoo_example(self):
        # Moon 18Cn / Jupiter 21Pi ithasala, Saturn 19Cn cancels.
        from jhora.calc.tajaka_yoga import tajaka_yogas
        cd = _syn_chart({Graha.SUN: 0.0, Graha.MOON: 108.0,
                         Graha.MARS: 300.0, Graha.MERCURY: 300.0,
                         Graha.JUPITER: 351.0, Graha.VENUS: 300.0,
                         Graha.SATURN: 109.0}, lagna=0.0)
        out = tajaka_yogas(cd)
        pair = [r for r in out.ithasalas
                if {r.g1, r.g2} == {Graha.MOON, Graha.JUPITER}]
        assert len(pair) == 1
        assert pair[0].manahoo_by == Graha.SATURN
