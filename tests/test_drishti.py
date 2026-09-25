"""Tests for houses-from-lagna drishti helper (engine covered elsewhere)."""

from jhora.calc.drishti import (ALL_GRAHAS, aspect_houses, aspects_from,
                                houses_aspected)
from jhora.types.graha import Graha


class TestHouses:
    def test_mars_from_lagna(self):
        # Mars in Aries (signs 3,6,7), lagna Leo (sign 4), ascending.
        assert houses_aspected(Graha.MARS, 0, 4) == [3, 4, 12]

    def test_all_grahas_covered(self):
        assert set(ALL_GRAHAS) == set(Graha)

    def test_nodes_trines(self):
        assert aspect_houses(Graha.RAHU) == (5, 7, 9)
        assert [a.target_sign_index for a in aspects_from(Graha.KETU, 0)] == [
            4, 6, 8]
