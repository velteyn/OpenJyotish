"""Tests for gandanta — junction zones, hand-checked boundaries."""

from jhora.calc.gandanta import (gandanta_planets, gandanta_zone,
                                 is_gandanta)
from jhora.types.graha import Graha


class TestZones:
    def test_end_water(self):
        # Cancer 26°40' is in; a minute before is out.
        assert gandanta_zone(3 * 30 + 26 + 2 / 3) == "end-Cancer"
        assert gandanta_zone(3 * 30 + 26 + 2 / 3 - 0.02) is None
        assert gandanta_zone(11 * 30 + 29.99) == "end-Pisces"
        assert gandanta_zone(7 * 30 + 27.5) == "end-Scorpio"

    def test_start_fire(self):
        assert gandanta_zone(0.0) == "start-Aries"
        assert gandanta_zone(4 * 30 + 3.0) == "start-Leo"
        assert gandanta_zone(8 * 30 + 10 / 3 - 0.01) == "start-Sagittarius"
        # Exactly 3°20' is out (strictly below).
        assert gandanta_zone(10 / 3) is None

    def test_middle_safe(self):
        assert not is_gandanta(15.0)
        assert not is_gandanta(5 * 30 + 15.0)
        assert not is_gandanta(1 * 30 + 29.0)  # Taurus end: not water


class TestPlanets:
    def test_map(self):
        lons = {Graha.MOON: 3 * 30 + 28.0, Graha.SUN: 100.0}
        assert gandanta_planets(lons) == {Graha.MOON: "end-Cancer"}
