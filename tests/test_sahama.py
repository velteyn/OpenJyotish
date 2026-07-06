import unittest
from jhora.types.graha import Graha
from jhora.calc.sahama import compute_sahamas, Sahama


class TestSahama(unittest.TestCase):

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
            Graha.KETU:    {"longitude": 10.0},
        }
        self.lagna_lon = 10.0

    def test_returns_36_sahamas(self):
        s = compute_sahamas(self.lagna_lon, self.planets)
        self.assertEqual(len(s), 36)

    def test_returns_sahama_instances(self):
        s = compute_sahamas(self.lagna_lon, self.planets)
        for sah in s:
            self.assertIsInstance(sah, Sahama)

    def test_longitude_in_range(self):
        s = compute_sahamas(self.lagna_lon, self.planets)
        for sah in s:
            self.assertGreaterEqual(sah.longitude, 0.0)
            self.assertLess(sah.longitude, 360.0)

    def test_name_not_empty(self):
        s = compute_sahamas(self.lagna_lon, self.planets)
        for sah in s:
            self.assertTrue(len(sah.name) > 0)

    def test_meaning_not_empty(self):
        s = compute_sahamas(self.lagna_lon, self.planets)
        for sah in s:
            self.assertTrue(len(sah.meaning) > 0)

    def test_punya_sahama(self):
        s = compute_sahamas(self.lagna_lon, self.planets)
        punya = [x for x in s if x.name == "Punya"][0]
        moon_lon = 45.0
        sun_lon = 5.0
        expected = (moon_lon - sun_lon + self.lagna_lon) % 360
        self.assertAlmostEqual(punya.longitude, expected, places=4)

    def test_artha_sahama_night(self):
        planets = {
            Graha.SUN:     {"longitude": 0.0},
            Graha.MOON:    {"longitude": 345.23333},
            Graha.MARS:    {"longitude": 354.96667},
            Graha.MERCURY: {"longitude": 311.46667},
            Graha.JUPITER: {"longitude": 0.0},
            Graha.VENUS:   {"longitude": 0.0},
            Graha.SATURN:  {"longitude": 19.16667},
            Graha.RAHU:    {"longitude": 0.0},
            Graha.KETU:    {"longitude": 0.0},
        }
        lagna_lon = 280.83333
        s = compute_sahamas(lagna_lon, planets, day=False)
        artha = [x for x in s if x.name == "Artha"][0]
        expected = 212.5
        self.assertAlmostEqual(artha.longitude, expected, places=1)

    def test_samartha_night_matches_helpfile(self):
        planets = {
            Graha.SUN:     {"longitude": 0.0},
            Graha.MOON:    {"longitude": 345.23333},
            Graha.MARS:    {"longitude": 354.96667},
            Graha.MERCURY: {"longitude": 311.46667},
            Graha.JUPITER: {"longitude": 0.0},
            Graha.VENUS:   {"longitude": 0.0},
            Graha.SATURN:  {"longitude": 19.16667},
            Graha.RAHU:    {"longitude": 0.0},
            Graha.KETU:    {"longitude": 0.0},
        }
        lagna_lon = 280.83333
        s = compute_sahamas(lagna_lon, planets, day=False)
        samartha = [x for x in s if x.name == "Samartha"][0]
        expected = 335.03333
        self.assertAlmostEqual(samartha.longitude, expected, places=1)

    def test_vanik_night_matches_helpfile(self):
        planets = {
            Graha.SUN:     {"longitude": 0.0},
            Graha.MOON:    {"longitude": 345.23333},
            Graha.MARS:    {"longitude": 354.96667},
            Graha.MERCURY: {"longitude": 311.46667},
            Graha.JUPITER: {"longitude": 0.0},
            Graha.VENUS:   {"longitude": 0.0},
            Graha.SATURN:  {"longitude": 19.16667},
            Graha.RAHU:    {"longitude": 0.0},
            Graha.KETU:    {"longitude": 0.0},
        }
        lagna_lon = 280.83333
        s = compute_sahamas(lagna_lon, planets, day=False)
        vanik = [x for x in s if x.name == "Vanik"][0]
        expected = 247.06667
        self.assertAlmostEqual(vanik.longitude, expected, places=1)

    def test_day_night_different(self):
        day = compute_sahamas(self.lagna_lon, self.planets, day=True)
        night = compute_sahamas(self.lagna_lon, self.planets, day=False)
        day_names = {s.name: s.longitude for s in day}
        night_names = {s.name: s.longitude for s in night}
        differing = [n for n in day_names if abs(day_names[n] - night_names[n]) > 0.01]
        self.assertGreater(len(differing), 0,
                           "Day and night should produce different results")

    def test_no_rev_same_day_night(self):
        day = compute_sahamas(self.lagna_lon, self.planets, day=True)
        night = compute_sahamas(self.lagna_lon, self.planets, day=False)
        day_names = {s.name: s.longitude for s in day}
        night_names = {s.name: s.longitude for s in night}
        samish = ["Bhratri", "Roga", "Mrityu", "Paradesa", "Artha",
                   "Vyapara", "Satru", "Labha"]
        for name in samish:
            self.assertAlmostEqual(day_names[name], night_names[name],
                                   places=4,
                                   msg=f"{name} should be same day/night")

    def test_all_sahamas_have_unique_names(self):
        s = compute_sahamas(self.lagna_lon, self.planets)
        names = [x.name for x in s]
        self.assertEqual(len(names), len(set(names)))

    def test_karyasiddhi_changes_at_night(self):
        s_day = compute_sahamas(self.lagna_lon, self.planets, day=True)
        s_night = compute_sahamas(self.lagna_lon, self.planets, day=False)
        k_day = {x.name: x.longitude for x in s_day}["Karyasiddhi"]
        k_night = {x.name: x.longitude for x in s_night}["Karyasiddhi"]
        self.assertNotAlmostEqual(k_day, k_night, places=2)
