"""Tests for Prasna (horary astrology) calculation.

Prasna determines a "Prasna Lagna" (query ascendant) from a user-supplied number.
Three modes:
  - Prasna-108 (mode 108):   N ∈ [1,108]  → fixes rasi + navamsa
  - Prasna-249 / KP (mode 249): N ∈ [1,249]  → fixes rasi + nakshatra + sub
  - Nadi Prasna (mode 1800): N ∈ [1,1800] → fixes rasi + nadyamsa (all shodasa vargas)
"""

import unittest
from jhora.calc.prasna import (
    PrasnaMode, PrasnaResult,
    compute_prasna_lagna, compute_prasna, all_prasna_results,
    _compute_108, _compute_249, _compute_nadi,
)
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra
from jhora.types.graha import Graha


class TestPrasnaModeEnum(unittest.TestCase):
    def test_max_number(self):
        self.assertEqual(PrasnaMode.MODE_108.max_number, 108)
        self.assertEqual(PrasnaMode.MODE_249.max_number, 249)
        self.assertEqual(PrasnaMode.NADI.max_number, 1800)

    def test_label(self):
        self.assertEqual(PrasnaMode.MODE_108.label, "Prasna-108")
        self.assertEqual(PrasnaMode.MODE_249.label, "Prasna-249 (KP)")
        self.assertEqual(PrasnaMode.NADI.label, "Nadi Prasna")


class TestMode108(unittest.TestCase):
    """Prasna-108: 12 rasis × 9 navamsas = 108 positions."""

    def test_position_1(self):
        """N=1 → rasi 0 (Aries), navamsa 0 → PL=0°."""
        r = compute_prasna(1, PrasnaMode.MODE_108)
        self.assertAlmostEqual(r.prasna_lagna, 0.0)
        self.assertEqual(r.rasi, Rasi.ARIES)
        self.assertEqual(r.navamsa_rasi, Rasi.ARIES)

    def test_position_9(self):
        """N=9 → rasi 0 (Aries), navamsa 8 → PL=26.6667°."""
        r = compute_prasna(9, PrasnaMode.MODE_108)
        self.assertAlmostEqual(r.prasna_lagna, 26.6666667)
        self.assertEqual(r.rasi, Rasi.ARIES)
        self.assertEqual(r.navamsa_rasi, Rasi.SAGITTARIUS)

    def test_position_10(self):
        """N=10 → rasi 1 (Taurus), navamsa 0 → PL=30°."""
        r = compute_prasna(10, PrasnaMode.MODE_108)
        self.assertAlmostEqual(r.prasna_lagna, 30.0)
        self.assertEqual(r.rasi, Rasi.TAURUS)
        self.assertEqual(r.navamsa_rasi, Rasi.VIRGO)

    def test_position_54(self):
        """N=54 → rasi 5 (Virgo), navamsa 8 → PL=176.6667°."""
        r = compute_prasna(54, PrasnaMode.MODE_108)
        self.assertAlmostEqual(r.prasna_lagna, 176.6666667)
        self.assertEqual(r.rasi, Rasi.VIRGO)
        self.assertEqual(r.navamsa_rasi, Rasi.VIRGO)

    def test_position_108(self):
        """N=108 → rasi 11 (Pisces), navamsa 8 → PL=356.6667°."""
        r = compute_prasna(108, PrasnaMode.MODE_108)
        self.assertAlmostEqual(r.prasna_lagna, 356.6666667)
        self.assertEqual(r.rasi, Rasi.PISCES)
        self.assertEqual(r.navamsa_rasi, Rasi.PISCES)

    def test_all_108_positions(self):
        """Verify 108 results exist, 9 per rasi."""
        results = all_prasna_results(PrasnaMode.MODE_108)
        self.assertEqual(len(results), 108)
        for rasi_idx in range(12):
            count = sum(1 for r in results if r.rasi.value == rasi_idx)
            self.assertEqual(count, 9, f"Rasi {Rasi(rasi_idx).name} has {count} positions (expected 9)")

    def test_each_rasi_degree_range(self):
        """For each rasi, PL ranges from rasi_start to rasi_end-3.333°."""
        results = all_prasna_results(PrasnaMode.MODE_108)
        for rasi_idx in range(12):
            ras = Rasi(rasi_idx)
            pls = sorted(r.prasna_lagna for r in results if r.rasi == ras)
            self.assertEqual(len(pls), 9)
            self.assertGreaterEqual(pls[0], rasi_idx * 30.0)
            self.assertLess(pls[-1], (rasi_idx + 1) * 30.0)

    def test_description(self):
        r = compute_prasna(1, PrasnaMode.MODE_108)
        self.assertIn("Rasi #1, Navamsa #1", r.description)
        self.assertIn("fixes rasi + navamsa", r.description)
        r = compute_prasna(108, PrasnaMode.MODE_108)
        self.assertIn("Rasi #12, Navamsa #9", r.description)

    def test_navamsa_odd_even_pattern(self):
        """Odd rasis (0-indexed even): navamsa_rasi = (rasi+nav)%12.
        Even rasis (0-indexed odd): navamsa_rasi = (rasi+4+nav)%12."""
        for rasi_idx in range(12):
            for nav_idx in range(9):
                n = rasi_idx * 9 + nav_idx + 1
                r = compute_prasna(n, PrasnaMode.MODE_108)
                if rasi_idx % 2 == 0:
                    expected = (rasi_idx + nav_idx) % 12
                else:
                    expected = (rasi_idx + 4 + nav_idx) % 12
                self.assertEqual(
                    r.navamsa_rasi.value, expected,
                    f"N={n} rasi={Rasi(rasi_idx).name} nav={nav_idx+1}: "
                    f"got {r.navamsa_rasi.name}, expected {Rasi(expected).name}"
                )

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            compute_prasna(0, PrasnaMode.MODE_108)
        with self.assertRaises(ValueError):
            compute_prasna(109, PrasnaMode.MODE_108)
        with self.assertRaises(ValueError):
            compute_prasna(-1, PrasnaMode.MODE_108)


class TestMode249(unittest.TestCase):
    """Prasna-249 (KP): 27 nakshatras × 9 Vimsottari-proportioned subs."""

    def test_position_1(self):
        """N=1 → Ashwini-1 (Sun sub): PL=0.3333° (center of 0°-0.6667°)."""
        r = compute_prasna(1, PrasnaMode.MODE_249)
        self.assertAlmostEqual(r.prasna_lagna, 0.3333, places=3)
        self.assertEqual(r.rasi, Rasi.ARIES)
        self.assertEqual(r.nakshatra, Nakshatra.ASVINI)
        self.assertEqual(r.sub_lord, Graha.SUN)

    def test_position_9(self):
        """N=9 → Ashwini-9 (Venus sub): PL=12.2222°
        (8×40' + 66.67' + 46.67' + 120' + 106.67' + 126.67' + 113.33' + 46.67') + 1/2×133.33'
        = 666.67' + 66.67' = 733.34' = 12.2222°"""
        r = compute_prasna(9, PrasnaMode.MODE_249)
        self.assertAlmostEqual(r.prasna_lagna, 12.2222, places=3)
        self.assertEqual(r.sub_lord, Graha.VENUS)

    def test_position_10(self):
        """N=10 → Bharani-1 (Sun sub): PL=13.6667°
        = 13.3333° + 0.3333°"""
        r = compute_prasna(10, PrasnaMode.MODE_249)
        self.assertAlmostEqual(r.prasna_lagna, 13.6667, places=3)
        self.assertEqual(r.nakshatra, Nakshatra.BHARANI)

    def test_position_243(self):
        """N=243 → Revati-9 (Venus sub): PL=358.8889°
        = 26×13.3333° + full Ashwini 8 subs + 1/2 × Venus sub size."""
        r = compute_prasna(243, PrasnaMode.MODE_249)
        self.assertAlmostEqual(r.prasna_lagna, 358.8889, places=3)
        self.assertEqual(r.nakshatra, Nakshatra.REVATI)
        self.assertEqual(r.sub_lord, Graha.VENUS)

    def test_position_244_wraps(self):
        """N=244 wraps to Ashwini-1 (like N=1 but same position)."""
        r = compute_prasna(244, PrasnaMode.MODE_249)
        self.assertAlmostEqual(r.prasna_lagna, 0.3333, places=3)
        self.assertEqual(r.nakshatra, Nakshatra.ASVINI)

    def test_all_249_positions(self):
        results = all_prasna_results(PrasnaMode.MODE_249)
        self.assertEqual(len(results), 249)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            compute_prasna(0, PrasnaMode.MODE_249)
        with self.assertRaises(ValueError):
            compute_prasna(250, PrasnaMode.MODE_249)
        with self.assertRaises(ValueError):
            compute_prasna(-5, PrasnaMode.MODE_249)

    def test_description(self):
        r = compute_prasna(1, PrasnaMode.MODE_249)
        self.assertIn("Nakshatra #1 (Asvini), Sub #1 (Sun)", r.description)
        self.assertIn("fixes rasi + nakshatra + sub", r.description)

    def test_sub_lords_cycle(self):
        """Sub lords should cycle through the 9 planets in Vimsottari order."""
        expected_order = [
            Graha.SUN, Graha.MOON, Graha.MARS, Graha.RAHU,
            Graha.JUPITER, Graha.SATURN, Graha.MERCURY, Graha.KETU, Graha.VENUS,
        ]
        for sub_idx, expected in enumerate(expected_order):
            n = sub_idx + 1  # position 1-9 within Ashwini
            r = compute_prasna(n, PrasnaMode.MODE_249)
            self.assertEqual(
                r.sub_lord, expected,
                f"Position {n}: expected sub {expected.name}, got {r.sub_lord.name}"
            )


class TestNadiMode(unittest.TestCase):
    """Nadi Prasna: 12 rasis × 150 nadyamsas = 1800 positions."""

    def test_position_1(self):
        """N=1 → rasi 0 (Aries), nadyamsa 1: PL=0.1° (center of 0°-0.2°)."""
        r = compute_prasna(1, PrasnaMode.NADI)
        self.assertAlmostEqual(r.prasna_lagna, 0.1)
        self.assertEqual(r.rasi, Rasi.ARIES)

    def test_position_150(self):
        """N=150 → last of Aries: PL=29.9°."""
        r = compute_prasna(150, PrasnaMode.NADI)
        self.assertAlmostEqual(r.prasna_lagna, 29.9)
        self.assertEqual(r.rasi, Rasi.ARIES)

    def test_position_151(self):
        """N=151 → rasi 1 (Taurus): PL=30.1°."""
        r = compute_prasna(151, PrasnaMode.NADI)
        self.assertAlmostEqual(r.prasna_lagna, 30.1)
        self.assertEqual(r.rasi, Rasi.TAURUS)

    def test_position_1800(self):
        """N=1800 → rasi 11 (Pisces), last nadyamsa: PL=359.9°."""
        r = compute_prasna(1800, PrasnaMode.NADI)
        self.assertAlmostEqual(r.prasna_lagna, 359.9)
        self.assertEqual(r.rasi, Rasi.PISCES)

    def test_all_1800_positions(self):
        results = all_prasna_results(PrasnaMode.NADI)
        self.assertEqual(len(results), 1800)
        for rasi_idx in range(12):
            count = sum(1 for r in results if r.rasi.value == rasi_idx)
            self.assertEqual(count, 150, f"Rasi {Rasi(rasi_idx).name} has {count} positions (expected 150)")

    def test_nadyamsa_resolution(self):
        """Each nadyamsa = 0.2° = 12 arcminutes."""
        r1 = compute_prasna(1, PrasnaMode.NADI)
        r2 = compute_prasna(2, PrasnaMode.NADI)
        self.assertAlmostEqual(r2.prasna_lagna - r1.prasna_lagna, 0.2)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            compute_prasna(0, PrasnaMode.NADI)
        with self.assertRaises(ValueError):
            compute_prasna(1801, PrasnaMode.NADI)

    def test_description(self):
        r = compute_prasna(1, PrasnaMode.NADI)
        self.assertIn("Rasi #1, Nadyamsa #1", r.description)
        self.assertIn("fixes all shodasa vargas", r.description)
        r = compute_prasna(1800, PrasnaMode.NADI)
        self.assertIn("Rasi #12, Nadyamsa #150", r.description)


class TestCoreFunctions(unittest.TestCase):
    """Direct tests of the internal compute_* functions."""

    def test_compute_108(self):
        self.assertAlmostEqual(_compute_108(1), 0.0)
        self.assertAlmostEqual(_compute_108(10), 30.0)
        self.assertAlmostEqual(_compute_108(55), 180.0)

    def test_compute_249(self):
        self.assertAlmostEqual(_compute_249(1), 0.3333, places=3)
        self.assertAlmostEqual(_compute_249(10), 13.6667, places=3)

    def test_compute_nadi(self):
        self.assertAlmostEqual(_compute_nadi(1), 0.1)
        self.assertAlmostEqual(_compute_nadi(151), 30.1)

    def test_compute_prasna_lagna_dispatcher(self):
        l108 = compute_prasna_lagna(1, PrasnaMode.MODE_108)
        self.assertAlmostEqual(l108, 0.0)
        l249 = compute_prasna_lagna(1, PrasnaMode.MODE_249)
        self.assertAlmostEqual(l249, 0.3333, places=3)
        l1800 = compute_prasna_lagna(1, PrasnaMode.NADI)
        self.assertAlmostEqual(l1800, 0.1)


class TestPrasnaResult(unittest.TestCase):
    """PrasnaResult data class properties."""

    def test_label_property(self):
        r = compute_prasna(1, PrasnaMode.MODE_108)
        self.assertEqual(r.label, "Prasna-108 (#1)")
        r = compute_prasna(249, PrasnaMode.MODE_249)
        self.assertEqual(r.label, "Prasna-249 (KP) (#249)")
        r = compute_prasna(1800, PrasnaMode.NADI)
        self.assertEqual(r.label, "Nadi Prasna (#1800)")

    def test_result_is_frozen(self):
        r = compute_prasna(1, PrasnaMode.MODE_108)
        with self.assertRaises(AttributeError):
            r.prasna_lagna = 99.0

    def test_degrees_in_rasi(self):
        for rasi_idx in range(12):
            n = rasi_idx * 9 + 1
            r = compute_prasna(n, PrasnaMode.MODE_108)
            self.assertAlmostEqual(r.degrees_in_rasi, r.prasna_lagna % 30)
            self.assertLess(r.degrees_in_rasi, 30.0)

    def test_nakshatra_pada(self):
        """Verify nakshatra pada is derived from longitude."""
        for n in [1, 50, 100]:
            r = compute_prasna(n, PrasnaMode.MODE_108)
            _, expected_pada = Nakshatra.from_longitude(r.prasna_lagna)
            self.assertEqual(r.nakshatra_pada, expected_pada)


class TestDisplayPLag(unittest.TestCase):
    """Prasna Lagna (PLag) replaces / augments natural Lagna."""

    def test_make_prasna_lagna_data(self):
        from jhora.calc.prasna import make_prasna_lagna_data
        from jhora.charts.chart import PlanetChartData

        pl = 45.0
        pld = make_prasna_lagna_data(pl)
        self.assertIsInstance(pld, PlanetChartData)
        self.assertEqual(pld.longitude, 45.0)
        self.assertEqual(pld.rasi, Rasi.TAURUS)
        self.assertEqual(pld.dignity, "prasna_lagna")


if __name__ == "__main__":
    unittest.main()
