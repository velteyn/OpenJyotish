"""Tests for Balaadi avasthas — hand-checked odd/even bands."""

from jhora.calc.avastha import (avastha_of, avasthas, balaadi_avastha)
from jhora.types.graha import Graha


class TestBands:
    def test_odd_sign_forward(self):
        assert balaadi_avastha(2.0) == ("Bala", "1/4")      # Ar 0-6
        assert balaadi_avastha(8.0) == ("Kumara", "1/2")    # Ar 6-12
        assert balaadi_avastha(15.0) == ("Yuva", "full")    # Ar 12-18
        assert balaadi_avastha(20.0) == ("Vriddha", "negligible")
        assert balaadi_avastha(29.0) == ("Mrita", "nil")

    def test_even_sign_reversed(self):
        assert balaadi_avastha(30 + 2.0)[0] == "Mrita"      # Ta 0-6
        assert balaadi_avastha(30 + 15.0)[0] == "Yuva"      # Ta 12-18
        assert balaadi_avastha(30 + 25.0)[0] == "Bala"      # Ta 24-30
        assert balaadi_avastha(60 + 13.0)[0] == "Yuva"      # Ge 12-18

    def test_band_edges(self):
        assert balaadi_avastha(6.0)[0] == "Kumara"
        assert balaadi_avastha(24.0)[0] == "Mrita"


class TestPlanets:
    def test_nodes_excluded(self):
        assert avastha_of(Graha.RAHU, 100.0) is None
        assert avastha_of(Graha.KETU, 100.0) is None

    def test_map_seven(self):
        lons = {Graha.SUN: 2.0, Graha.RAHU: 2.0}
        assert avasthas(lons) == {Graha.SUN: "Bala"}
