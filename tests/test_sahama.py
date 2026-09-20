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
        # Same-formula sahamas. Satru is deliberately NOT here: both
        # Hayanaratna ("the reverse at night") and Raman (unmarked, so
        # reversed) agree it reverses — see test_satru_reverses_at_night.
        samish = ["Bhratri", "Roga", "Mrityu", "Paradesa", "Artha",
                    "Vyapara", "Labha"]
        for name in samish:
            self.assertAlmostEqual(day_names[name], night_names[name],
                                    places=4,
                                    msg=f"{name} should be same day/night")

    def test_satru_reverses_at_night(self):
        day = {s.name: s.longitude
               for s in compute_sahamas(self.lagna_lon, self.planets,
                                        day=True)}
        night = {s.name: s.longitude
                 for s in compute_sahamas(self.lagna_lon, self.planets,
                                          day=False)}
        # Mars(65) − Saturn(310) + lagna(10) = 125 (no +30°: lagna
        # sits between subtrahend and minuend).
        self.assertAlmostEqual(day["Satru"], 125.0, places=4)
        # Night swaps to Saturn − Mars + lagna = 255, and the +30° rule
        # fires (lagna outside the span) → 285.
        self.assertAlmostEqual(night["Satru"], 285.0, places=4)

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

    def test_sahama_by_name(self):
        from jhora.calc.sahama import sahama_by_name
        s = compute_sahamas(self.lagna_lon, self.planets)
        punya = sahama_by_name(self.lagna_lon, self.planets, "punya")
        self.assertAlmostEqual(
            punya.longitude,
            [x for x in s if x.name == "Punya"][0].longitude, places=6)
        with self.assertRaises(KeyError):
            sahama_by_name(self.lagna_lon, self.planets, "Nope")


class TestIsDayBirth(unittest.TestCase):
    def _chart(self, hour):
        from jhora.charts.chart import ChartBuilder
        return ChartBuilder().build(
            year=1990, month=1, day=15, hour=hour,
            lat=12.9716, lon=77.5946, tz="+0530")

    def test_midday_is_day(self):
        from jhora.calc.sahama import is_day_birth
        self.assertTrue(is_day_birth(self._chart(12.0)))

    def test_midnight_is_night(self):
        from jhora.calc.sahama import is_day_birth
        self.assertFalse(is_day_birth(self._chart(2.0)))

    def test_predawn_uses_sunrise_not_clock(self):
        # 06:10 in mid-January Bangalore is before sunrise (~06:49):
        # the old 6:00–18:00 heuristic said day; geometry says night.
        from jhora.calc.sahama import is_day_birth
        self.assertFalse(is_day_birth(self._chart(6 + 10 / 60.0)))

    def test_cli_sahamas_runs(self):
        from typer.testing import CliRunner
        from jhora.cli.main import app
        out = CliRunner().invoke(
            app, ["sahamas", "1990-01-15 17:30:00 +0530 12.9716 77.5946"])
        assert out.exit_code == 0, out.output
        text = out.stdout
        self.assertIn("Punya", text)
        self.assertIn("Mrityu", text)
        self.assertIn("Labha", text)

    def test_tui_sahamas_action_runs(self):
        from jhora.charts.chart import ChartBuilder
        from jhora.tui.main import JhoraTui
        tui = JhoraTui()
        tui.chart = ChartBuilder().build(
            year=1990, month=1, day=15, hour=17.5,
            lat=12.9716, lon=77.5946, tz="+0530")
        tui._action_sahamas()
        blob = "\n".join(tui._content_lines)
        self.assertIn("Punya", blob)
        self.assertIn("Vivaha", blob)

    def test_html_export_has_sahamas(self):
        from jhora.charts.chart import ChartBuilder
        from jhora.export.report import _sahamas_table
        cd = ChartBuilder().build(
            year=1990, month=1, day=15, hour=17.5,
            lat=12.9716, lon=77.5946, tz="+0530")
        html = _sahamas_table(cd)
        self.assertIn("<h2>Sahamas (36,", html)
        self.assertIn("Punya", html)
        self.assertIn("Apamrityu", html)
