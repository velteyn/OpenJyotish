"""Tests for Graha Yuddha — hand-built pairs, no ephemeris needed."""

import pytest

from jhora.calc.yuddha import planetary_wars, separation, victor
from jhora.types.graha import Graha


class TestSeparation:
    def test_wrap(self):
        assert separation(359.8, 0.1) == pytest.approx(0.3)
        assert separation(10.0, 12.0) == pytest.approx(2.0)


class TestWar:
    def test_basic_pair(self):
        lons = {Graha.MARS: 100.0, Graha.JUPITER: 100.5}
        lats = {Graha.MARS: 1.0, Graha.JUPITER: 0.5}
        wars = planetary_wars(lons, lats)
        assert len(wars) == 1
        assert wars[0]["winner"] == Graha.MARS
        assert wars[0]["loser"] == Graha.JUPITER
        assert wars[0]["separation"] == 0.5

    def test_venus_beats_north(self):
        lons = {Graha.VENUS: 100.0, Graha.MARS: 100.4}
        lats = {Graha.VENUS: -1.0, Graha.MARS: 2.0}
        wars = planetary_wars(lons, lats)
        assert wars[0]["winner"] == Graha.VENUS

    def test_too_far_no_war(self):
        lons = {Graha.MARS: 100.0, Graha.JUPITER: 101.5}
        assert planetary_wars(lons, {}) == []

    def test_boundary_no_war(self):
        lons = {Graha.MARS: 100.0, Graha.JUPITER: 101.0}
        assert planetary_wars(lons, {}) == []

    def test_sun_moon_nodes_excluded(self):
        lons = {Graha.SUN: 100.0, Graha.MOON: 100.1,
                Graha.MARS: 100.2, Graha.RAHU: 100.3}
        assert planetary_wars(lons, {}) == []

    def test_latitude_tie_disc(self):
        win, _reason = victor((Graha.MERCURY, Graha.JUPITER),
                              {Graha.MERCURY: 0.5, Graha.JUPITER: 0.5})
        assert win == Graha.JUPITER
