"""Tests for combustion (Asta) — hand-computed elongations."""

from jhora.calc.combustion import (combust_planets, elongation, is_combust,
                                   orb)
from jhora.types.graha import Graha


class TestElongation:
    def test_wrap(self):
        assert elongation(359.0, 1.0) == 2.0
        assert elongation(10.0, 350.0) == 20.0
        assert elongation(180.0, 0.0) == 180.0


class TestOrbs:
    def test_standard_set(self):
        assert orb(Graha.MOON) == 12.0
        assert orb(Graha.MARS) == 17.0
        assert orb(Graha.MERCURY) == 14.0
        assert orb(Graha.MERCURY, True) == 12.0
        assert orb(Graha.JUPITER) == 11.0
        assert orb(Graha.VENUS) == 10.0
        assert orb(Graha.VENUS, True) == 8.0
        assert orb(Graha.SATURN) == 15.0

    def test_never_burnt(self):
        assert orb(Graha.SUN) is None
        assert orb(Graha.RAHU) is None
        assert orb(Graha.KETU) is None


class TestCombust:
    def test_inside(self):
        assert is_combust(Graha.MERCURY, 100.0, 110.0)  # 10 < 14

    def test_outside(self):
        assert not is_combust(Graha.SATURN, 100.0, 116.0)  # 16 > 15

    def test_boundary_is_not_combust(self):
        assert not is_combust(Graha.JUPITER, 100.0, 111.0)  # == 11

    def test_retro_tighter_venus(self):
        assert is_combust(Graha.VENUS, 100.0, 107.0)  # 7 < 10 direct
        assert is_combust(Graha.VENUS, 100.0, 107.0, True)  # 7 < 8 retro
        assert not is_combust(Graha.VENUS, 100.0, 109.0, True)  # 9 > 8

    def test_nodes_never(self):
        assert not is_combust(Graha.RAHU, 100.0, 100.5)

    def test_map(self):
        lons = {Graha.MERCURY: 100.0, Graha.SATURN: 200.0}
        assert set(combust_planets(lons, 110.0)) == {Graha.MERCURY}
