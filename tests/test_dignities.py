"""Tests for DignityChecker in calc/dignities.py."""

import pytest

from jhora.calc.dignities import DignityChecker
from jhora.types.graha import Graha


@pytest.fixture
def dc():
    return DignityChecker()


class TestExaltation:
    def test_sun_exalted(self, dc):
        """Sun exalted at 10° Aries (sign 0)."""
        assert dc.get_dignity(Graha.SUN, 0, 10.0) == "exalted"

    def test_sun_near_exalted(self, dc):
        """Sun near exaltation degree (±5°)."""
        assert dc.get_dignity(Graha.SUN, 0, 12.0) == "exalted"
        assert dc.get_dignity(Graha.SUN, 0, 8.0) == "exalted"

    def test_sun_past_exaltation_range(self, dc):
        """Sun past the ±5° orb should not be exalted."""
        assert dc.get_dignity(Graha.SUN, 0, 16.0) != "exalted"

    def test_moon_exalted(self, dc):
        """Moon exalted at 3° Taurus (sign 1)."""
        assert dc.get_dignity(Graha.MOON, 1, 3.0) == "exalted"

    def test_jupiter_exalted(self, dc):
        """Jupiter exalted at 5° Cancer (sign 3)."""
        assert dc.get_dignity(Graha.JUPITER, 3, 5.0) == "exalted"

    def test_saturn_exalted(self, dc):
        """Saturn exalted at 20° Libra (sign 6)."""
        assert dc.get_dignity(Graha.SATURN, 6, 20.0) == "exalted"


class TestDebilitation:
    def test_sun_debilitated(self, dc):
        """Sun debilitated at 10° Libra (sign 6)."""
        assert dc.get_dignity(Graha.SUN, 6, 10.0) == "debilitated"

    def test_moon_debilitated(self, dc):
        """Moon debilitated at 3° Scorpio (sign 7)."""
        assert dc.get_dignity(Graha.MOON, 7, 3.0) == "debilitated"

    def test_mars_debilitated(self, dc):
        """Mars debilitated at 28° Cancer (sign 3)."""
        assert dc.get_dignity(Graha.MARS, 3, 28.0) == "debilitated"

    def test_jupiter_debilitated(self, dc):
        """Jupiter debilitated at 5° Capricorn (sign 9)."""
        assert dc.get_dignity(Graha.JUPITER, 9, 5.0) == "debilitated"


class TestMoolatrikona:
    def test_sun_moolatrikona(self, dc):
        """Sun moolatrikona in Leo (sign 4), 0-20°."""
        assert dc.get_dignity(Graha.SUN, 4, 10.0) == "moolatrikona"

    def test_sun_beyond_moolatrikona(self, dc):
        """Sun in Leo beyond 20° is own sign, not moolatrikona."""
        assert dc.get_dignity(Graha.SUN, 4, 25.0) == "own"

    def test_mars_moolatrikona(self, dc):
        """Mars moolatrikona in Aries (sign 0), 0-12°."""
        assert dc.get_dignity(Graha.MARS, 0, 5.0) == "moolatrikona"

    def test_mars_past_moolatrikona(self, dc):
        """Mars in Aries past 12° is own sign."""
        assert dc.get_dignity(Graha.MARS, 0, 15.0) == "own"


class TestOwnSign:
    def test_sun_own_leo(self, dc):
        assert dc.get_dignity(Graha.SUN, 4, 25.0) == "own"

    def test_moon_own_cancer(self, dc):
        assert dc.get_dignity(Graha.MOON, 3, 10.0) == "own"

    def test_mars_own_scorpio(self, dc):
        assert dc.get_dignity(Graha.MARS, 7, 10.0) == "own"

    def test_mercury_own_gemini(self, dc):
        assert dc.get_dignity(Graha.MERCURY, 2, 10.0) == "own"

    def test_venus_moolatrikona_libra(self, dc):
        """Venus at 10° Libra → moolatrikona (Libra 0-15° is Venus' moolatrikona)."""
        assert dc.get_dignity(Graha.VENUS, 6, 10.0) == "moolatrikona"

    def test_saturn_moolatrikona_aquarius(self, dc):
        """Saturn at 10° Aquarius → moolatrikona (Aquarius 0-20° is Saturn's moolatrikona)."""
        assert dc.get_dignity(Graha.SATURN, 10, 10.0) == "moolatrikona"


class TestNeutral:
    def test_venus_in_aries(self, dc):
        """Venus in Aries — no special dignity."""
        assert dc.get_dignity(Graha.VENUS, 0, 15.0) == "neutral"

    def test_mars_in_gemini(self, dc):
        """Mars in Gemini — neutral."""
        assert dc.get_dignity(Graha.MARS, 2, 10.0) == "neutral"


class TestReferenceChart:
    """Verify dignity assignments from our reference chart (1970-04-04)."""

    @pytest.fixture(autouse=True)
    def setup(self, dc):
        self.dc = dc

    def test_sun_neutral_reference(self):
        """Sun at 21.10° Pisces (sidereal) → neutral."""
        assert self.dc.get_dignity(Graha.SUN, 11, 21.10) == "neutral"

    def test_mars_moolatrikona_reference(self):
        """Mars at 3.56° Aries (sidereal) → moolatrikona (Aries 0-12°)."""
        assert self.dc.get_dignity(Graha.MARS, 0, 3.56) == "moolatrikona"

    def test_venus_moolatrikona_reference(self):
        """Venus at 9.74° Libra (sidereal) → moolatrikona (Libra 0-15°)."""
        assert self.dc.get_dignity(Graha.VENUS, 6, 9.74) == "moolatrikona"

    def test_saturn_debilitated_reference(self):
        """Saturn at 15.12° Aries (sidereal) → debilitated (within 5° of Aries 20°)."""
        assert self.dc.get_dignity(Graha.SATURN, 0, 15.12) == "debilitated"
