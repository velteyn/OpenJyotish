import unittest
from jhora.types.graha import Graha
from jhora.charts.chart import ChartBuilder
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

    def test_ak_is_highest_in_sign(self):
        """Atma Karaka = most degrees traversed within its sign (Me 25°)."""
        k = compute_chara_karakas(self.planets)
        self.assertEqual(k[0].graha, Graha.MERCURY)
        self.assertEqual(k[0].short_name, "AK")

    def test_dk_is_lowest_in_sign(self):
        """Dara Karaka = fewest in-sign degrees (Ma 5°, after Su 5% tie
        resolved by input order)."""
        k = compute_chara_karakas(self.planets)
        self.assertEqual(k[-1].graha, Graha.MARS)
        self.assertEqual(k[-1].short_name, "DK")

    def test_sorted_descending_in_sign(self):
        k = compute_chara_karakas(self.planets)
        degs = [p.longitude % 30 for p in k]
        for i in range(len(degs) - 1):
            self.assertGreaterEqual(degs[i], degs[i + 1])

    def test_karaka_rank_property(self):
        k = compute_chara_karakas(self.planets)
        for i, karaka in enumerate(k):
            self.assertEqual(karaka.rank, i + 1)

    def test_karaka_names(self):
        k = compute_chara_karakas(self.planets)
        expected = ["AK", "AmK", "BK", "MK", "PiK", "PutK", "GnK", "DK"]
        for karaka, exp in zip(k, expected):
            self.assertEqual(karaka.short_name, exp)

    def test_putra_before_gnati_before_dara(self):
        """8-karaka order: PutK(6th) Ra, GnK(7th) Su, DK(8th) Ma."""
        k = compute_chara_karakas(self.planets)
        by_name = {karaka.short_name: karaka.graha for karaka in k}
        self.assertEqual(by_name["PutK"], Graha.RAHU)
        self.assertEqual(by_name["GnK"], Graha.SUN)
        self.assertEqual(by_name["DK"], Graha.MARS)

    def test_karaka_meaning_not_empty(self):
        k = compute_chara_karakas(self.planets)
        for karaka in k:
            self.assertTrue(len(karaka.meaning) > 0,
                            f"{karaka.short_name} has empty meaning")

    def test_get_atma_karaka(self):
        ak = get_atma_karaka(self.planets)
        self.assertEqual(ak.graha, Graha.MERCURY)
        self.assertEqual(ak.short_name, "AK")

    def test_user_chart_dara_is_jupiter(self):
        """Regression: 1973-03-13 Padua must yield DK Jupiter (lowest
        in-sign degrees), not Moon — the old absolute-longitude sort fed
        every AI answer a wrong Dara Karaka."""
        builder = ChartBuilder()
        cd = builder.build(1973, 3, 13, 13 + 55 / 60,
                           lat=45.4130, lon=11.8806, tz="+0100")
        planets = {g: {"longitude": p.longitude}
                   for g, p in cd.planets.items()}
        by_name = {k.short_name: k.graha
                   for k in compute_chara_karakas(planets)}
        self.assertEqual(by_name["DK"], Graha.JUPITER)
        self.assertEqual(by_name["AmK"], Graha.SUN)

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
