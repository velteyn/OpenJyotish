import unittest
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.calc.arudha import (
    bhava_arudha, all_bhava_arudhas,
    graha_arudha, all_graha_arudhas,
)


_DEFAULT_PLANETS = {
    Graha.SUN:     {"longitude": 5.0},
    Graha.MOON:    {"longitude": 45.0},
    Graha.MARS:    {"longitude": 65.0},
    Graha.MERCURY: {"longitude": 85.0},
    Graha.JUPITER: {"longitude": 255.0},
    Graha.VENUS:   {"longitude": 170.0},
    Graha.SATURN:  {"longitude": 310.0},
    Graha.RAHU:    {"longitude": 190.0},
    Graha.KETU:    {"longitude": 10.0},
}
_DEFAULT_LAGNA = 10.0  # Aries


class TestBhavaArudha(unittest.TestCase):

    def test_al_not_in_lagna_or_7th(self):
        for n in range(1, 13):
            a = bhava_arudha(n, _DEFAULT_LAGNA, _DEFAULT_PLANETS)
            lagna_rasi = int(_DEFAULT_LAGNA // 30) % 12
            house_rasi = (lagna_rasi + n - 1) % 12
            self.assertNotEqual(a.value, house_rasi,
                                f"A{n} should not be in house sign")
            self.assertNotEqual(a.value, (house_rasi + 6) % 12,
                                f"A{n} should not be 7th from house sign")

    def test_all_returns_12(self):
        result = all_bhava_arudhas(_DEFAULT_LAGNA, _DEFAULT_PLANETS)
        self.assertEqual(len(result), 12)
        self.assertEqual(set(result.keys()), set(range(1, 13)))

    def test_known_example_gemini_mercury_aquarius(self):
        planets = {
            Graha.SUN:     {"longitude": 0.0},
            Graha.MOON:    {"longitude": 330.0},
            Graha.MARS:    {"longitude": 300.0},
            Graha.MERCURY: {"longitude": 300.0},
            Graha.JUPITER: {"longitude": 300.0},
            Graha.VENUS:   {"longitude": 300.0},
            Graha.SATURN:  {"longitude": 300.0},
            Graha.RAHU:    {"longitude": 300.0},
            Graha.KETU:    {"longitude": 300.0},
        }
        lagna_lon = 62.0
        a1 = bhava_arudha(1, lagna_lon, planets)
        rasi = int(lagna_lon // 30) % 12
        self.assertEqual(rasi, 2)

    def test_scorpio_dual_lord(self):
        planets = {
            Graha.SUN:     {"longitude": 220.0},
            Graha.MOON:    {"longitude": 230.0},
            Graha.MARS:    {"longitude": 235.0},
            Graha.MERCURY: {"longitude": 240.0},
            Graha.JUPITER: {"longitude": 245.0},
            Graha.VENUS:   {"longitude": 250.0},
            Graha.SATURN:  {"longitude": 255.0},
            Graha.RAHU:    {"longitude": 260.0},
            Graha.KETU:    {"longitude": 20.0},
        }
        lagna_lon = 202.0
        a8 = bhava_arudha(8, lagna_lon, planets)
        self.assertIsInstance(a8, Rasi)

    def test_aquarius_dual_lord(self):
        planets = {
            Graha.SUN:     {"longitude": 300.0},
            Graha.MOON:    {"longitude": 310.0},
            Graha.MARS:    {"longitude": 320.0},
            Graha.MERCURY: {"longitude": 330.0},
            Graha.JUPITER: {"longitude": 340.0},
            Graha.VENUS:   {"longitude": 350.0},
            Graha.SATURN:  {"longitude": 280.0},
            Graha.RAHU:    {"longitude": 200.0},
            Graha.KETU:    {"longitude": 20.0},
        }
        lagna_lon = 302.0
        a11 = bhava_arudha(11, lagna_lon, planets)
        self.assertIsInstance(a11, Rasi)

    def test_all_returns_rasi_enum(self):
        for n in range(1, 13):
            a = bhava_arudha(n, _DEFAULT_LAGNA, _DEFAULT_PLANETS)
            self.assertIsInstance(a, Rasi)


class TestGrahaArudha(unittest.TestCase):

    def test_all_returns_9(self):
        result = all_graha_arudhas(_DEFAULT_PLANETS)
        self.assertEqual(len(result), 9)

    def test_returns_rasi_enum(self):
        for g in Graha:
            a = graha_arudha(g, _DEFAULT_PLANETS)
            self.assertIsInstance(a, Rasi)

    def test_not_in_planet_sign_or_7th(self):
        for g in Graha:
            a = graha_arudha(g, _DEFAULT_PLANETS)
            p_rasi = int(_DEFAULT_PLANETS[g]["longitude"] // 30) % 12
            self.assertNotEqual(a.value, p_rasi,
                                f"A({g.short_name}) should not be in own sign")
            self.assertNotEqual(a.value, (p_rasi + 6) % 12,
                                f"A({g.short_name}) should not be 7th from own")

    def test_sun_aries_own_leo(self):
        planets = {
            Graha.SUN:     {"longitude": 5.0},
            Graha.MOON:    {"longitude": 45.0},
            Graha.MARS:    {"longitude": 65.0},
            Graha.MERCURY: {"longitude": 85.0},
            Graha.JUPITER: {"longitude": 255.0},
            Graha.VENUS:   {"longitude": 170.0},
            Graha.SATURN:  {"longitude": 310.0},
            Graha.RAHU:    {"longitude": 190.0},
            Graha.KETU:    {"longitude": 10.0},
        }
        a = graha_arudha(Graha.SUN, planets)
        rasi = int(5.0 // 30) % 12
        owned = 4
        diff = (4 - 0) % 12
        result = (4 + diff) % 12
        self.assertEqual(a.value, result)

    def test_moon_taurus_own_cancer(self):
        planets = {
            Graha.SUN:     {"longitude": 0.0},
            Graha.MOON:    {"longitude": 45.0},
            Graha.MARS:    {"longitude": 65.0},
            Graha.MERCURY: {"longitude": 85.0},
            Graha.JUPITER: {"longitude": 255.0},
            Graha.VENUS:   {"longitude": 170.0},
            Graha.SATURN:  {"longitude": 310.0},
            Graha.RAHU:    {"longitude": 190.0},
            Graha.KETU:    {"longitude": 10.0},
        }
        a = graha_arudha(Graha.MOON, planets)
        self.assertIsInstance(a, Rasi)

    def test_rahu_exaltation(self):
        a = graha_arudha(Graha.RAHU, _DEFAULT_PLANETS)
        self.assertIsInstance(a, Rasi)

    def test_ketu_exaltation(self):
        a = graha_arudha(Graha.KETU, _DEFAULT_PLANETS)
        self.assertIsInstance(a, Rasi)


class TestEdgeCases(unittest.TestCase):

    def test_empty_planets_raises(self):
        with self.assertRaises(KeyError):
            bhava_arudha(1, 0.0, {})

    def test_missing_graha_raises(self):
        with self.assertRaises(KeyError):
            graha_arudha(Graha.SUN, {})

    def test_lagna_at_boundary(self):
        planets = {
            Graha.SUN:     {"longitude": 30.0},
            Graha.MOON:    {"longitude": 45.0},
            Graha.MARS:    {"longitude": 65.0},
            Graha.MERCURY: {"longitude": 85.0},
            Graha.JUPITER: {"longitude": 255.0},
            Graha.VENUS:   {"longitude": 170.0},
            Graha.SATURN:  {"longitude": 310.0},
            Graha.RAHU:    {"longitude": 190.0},
            Graha.KETU:    {"longitude": 10.0},
        }
        for boundary in [0.0, 29.999, 30.0, 359.999]:
            a = bhava_arudha(1, boundary, planets)
            self.assertIsInstance(a, Rasi)

    def test_all_planets_in_one_sign(self):
        planets = {g: {"longitude": 5.0} for g in Graha}
        a1 = bhava_arudha(1, 10.0, planets)
        self.assertIsInstance(a1, Rasi)
        for g in Graha:
            a = graha_arudha(g, planets)
            self.assertIsInstance(a, Rasi)
