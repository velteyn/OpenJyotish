"""Tests for special sensitive points (Baadhaka, Pushkara, Khara, 22nd)."""

from typer.testing import CliRunner

from jhora.calc.special_points import (
    baadhaka_lord, baadhaka_sthana, drekkana_22, khara_navamsa_64,
    planets_in_pushkara_bhaga, planets_in_pushkara_navamsa,
)
from jhora.cli.main import app
from jhora.types.graha import Graha

runner = CliRunner()
JALKOT = "2001-02-24 06:11:00 +0530 18.6333 77.2"


class TestBaadhaka:
    def test_movable_11th(self):
        assert baadhaka_sthana(0) == 10  # Aries → Aquarius

    def test_fixed_9th(self):
        assert baadhaka_sthana(1) == 9  # Taurus → Capricorn

    def test_dual_7th(self):
        assert baadhaka_sthana(2) == 8  # Gemini → Scorpio

    def test_lord(self):
        assert baadhaka_lord(0) == Graha.SATURN  # Aquarius lord
        assert baadhaka_lord(10) == Graha.VENUS  # Aquarius lagna → Libra


class TestPushkara:
    def test_navamsa_windows(self):
        # Aries: [20, 23.33) and [26.67, 30).
        assert Graha.SUN in planets_in_pushkara_navamsa({Graha.SUN: 21.0})
        assert Graha.SUN in planets_in_pushkara_navamsa({Graha.SUN: 28.0})
        assert planets_in_pushkara_navamsa({Graha.SUN: 10.0}) == []
        # Taurus: [6.67, 10) and [13.33, 16.67).
        assert Graha.MOON in planets_in_pushkara_navamsa({Graha.MOON: 38.0})
        assert planets_in_pushkara_navamsa({Graha.MOON: 40.0}) == []

    def test_bhaga_window(self):
        # Aries bhaga 21°: [20, 21).
        assert Graha.MARS in planets_in_pushkara_bhaga({Graha.MARS: 20.5})
        assert planets_in_pushkara_bhaga({Graha.MARS: 10.0}) == []


class TestKharaAndDrekkana:
    def test_jalkot_moon(self):
        # Moon 117.94 Cancer: navamsa Pisces → Khara Gemini;
        # drekkana Pisces → 22nd Libra.
        assert khara_navamsa_64(117.94) == 2
        assert drekkana_22(117.94) == 6


class TestSpecialPointsCli:
    def test_command(self):
        result = runner.invoke(app, ["special-points", JALKOT])
        assert result.exit_code == 0, result.output
        assert "Baadhaka sthana" in result.output
        assert "Pushkara navamsa" in result.output
        assert "64th navamsa" in result.output
