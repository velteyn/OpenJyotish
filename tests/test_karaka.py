import unittest
from jhora.types.graha import Graha
from jhora.calc.karaka import compute_chara_karakas, get_atma_karaka, CharaKaraka


class TestCharaKaraka(unittest.TestCase):

    def setUp(self):
        self.planets = {
            Graha.SUN:     {"longitude": 5.0},
            Graha.MOON:    {"longitude": 45.0},
            Graha.MARS:    {"longitude": 65.0},
            Graha.MERCURY: {"longitude": 85.0},
            Graha.JUPITER: {"longitude": 255.0},
            Graha.VENUS:   {"longitude": 170.0},
            Graha.SATURN:  {"longitude": 310.0},
            Graha.RAHU:    {"longitude": 190.0},
        }

    def test_returns_eight_karakas(self):
        k = compute_chara_karakas(self.planets)
        self.assertEqual(len(k), 8)

    def test_ak_is_highest_longitude(self):
        k = compute_chara_karakas(self.planets)
        self.assertEqual(k[0].graha, Graha.SATURN)
        self.assertEqual(k[0].short_name, "AK")

    def test_stk_is_lowest_longitude(self):
        k = compute_chara_karakas(self.planets)
        self.assertEqual(k[-1].graha, Graha.SUN)
        self.assertEqual(k[-1].short_name, "StK")

    def test_sorted_descending(self):
        k = compute_chara_karakas(self.planets)
        lons = [p.longitude for p in k]
        for i in range(len(lons) - 1):
            self.assertGreaterEqual(lons[i], lons[i + 1])

    def test_karaka_rank_property(self):
        k = compute_chara_karakas(self.planets)
        for i, karaka in enumerate(k):
            self.assertEqual(karaka.rank, i + 1)

    def test_karaka_names(self):
        k = compute_chara_karakas(self.planets)
        expected = ["AK", "AmK", "BK", "MK", "PiK", "GK", "DK", "StK"]
        for karaka, exp in zip(k, expected):
            self.assertEqual(karaka.short_name, exp)

    def test_karaka_meaning_not_empty(self):
        k = compute_chara_karakas(self.planets)
        for karaka in k:
            self.assertTrue(len(karaka.meaning) > 0,
                            f"{karaka.short_name} has empty meaning")

    def test_get_atma_karaka(self):
        ak = get_atma_karaka(self.planets)
        self.assertEqual(ak.graha, Graha.SATURN)
        self.assertEqual(ak.short_name, "AK")

    def test_excludes_ketu(self):
        planets_with_ketu = dict(self.planets)
        planets_with_ketu[Graha.KETU] = {"longitude": 300.0}
        k = compute_chara_karakas(planets_with_ketu)
        self.assertEqual(len(k), 8)
        for karaka in k:
            self.assertNotEqual(karaka.graha, Graha.KETU)

    def test_returns_chara_karaka_instances(self):
        k = compute_chara_karakas(self.planets)
        for karaka in k:
            self.assertIsInstance(karaka, CharaKaraka)

    def test_reversed_order(self):
        planets = {
            Graha.SUN:     {"longitude": 310.0},
            Graha.MOON:    {"longitude": 280.0},
            Graha.MARS:    {"longitude": 250.0},
            Graha.MERCURY: {"longitude": 220.0},
            Graha.JUPITER: {"longitude": 190.0},
            Graha.VENUS:   {"longitude": 160.0},
            Graha.SATURN:  {"longitude": 130.0},
            Graha.RAHU:    {"longitude": 100.0},
        }
        k = compute_chara_karakas(planets)
        self.assertEqual(k[0].graha, Graha.SUN)
        self.assertEqual(k[-1].graha, Graha.RAHU)

    def test_missing_planet_returns_fewer(self):
        incomplete = {Graha.SUN: {"longitude": 10.0}}
        k = compute_chara_karakas(incomplete)
        self.assertEqual(len(k), 1)

    def test_all_planets_same_longitude(self):
        planets = {g: {"longitude": 100.0} for g in
                   [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                    Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU]}
        k = compute_chara_karakas(planets)
        self.assertEqual(len(k), 8)
        self.assertEqual(k[0].longitude, 100.0)
        self.assertEqual(k[-1].longitude, 100.0)
