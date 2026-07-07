import unittest
from jhora.calc.tajaka import (
    compute_muntha,
    compute_harsha_bala,
    compute_patyayini_dasa,
    compute_mudda_dasa,
    _MUDDA_DAYS, _MUDDA_ORDER,
)
from jhora.types.graha import Graha
from jhora.charts.chart import ChartData, PlanetChartData
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra
from datetime import datetime


def _fake_planet(lon: float) -> PlanetChartData:
    rasi = Rasi(int(lon // 30) % 12)
    deg = lon % 30
    nak, pada = Nakshatra.from_longitude(lon)
    return PlanetChartData(
        graha=Graha.SUN, longitude=lon, latitude=0.0, speed=1.0,
        is_retrograde=False, rasi=rasi, degrees_in_rasi=deg,
        nakshatra=nak, nakshatra_pada=pada, dignity="normal",
    )


class TestMuntha(unittest.TestCase):

    def test_first_year_muntha_equals_natal_lagna(self):
        self.assertEqual(compute_muntha(3, 1), 3)

    def test_second_year_advances_one(self):
        self.assertEqual(compute_muntha(0, 2), 1)

    def test_wraps_after_12(self):
        self.assertEqual(compute_muntha(11, 2), 0)

    def test_large_year_number(self):
        self.assertEqual(compute_muntha(0, 25), 0)
        self.assertEqual(compute_muntha(3, 37), 3)


class TestHarshaBala(unittest.TestCase):

    def setUp(self):
        planets = {}
        for g in Graha:
            if g == Graha.KETU:
                continue
            planets[g] = _fake_planet(0.0)
        self.chart = ChartData(
            birth_date=datetime(2000, 1, 1),
            julian_day=2451545.0,
            latitude=0.0, longitude=0.0,
            timezone="UTC", ayanamsa_name="lahiri",
            ayanamsa_value=23.5,
            planets={g: planets.get(g, _fake_planet(0.0)) for g in Graha},
            lagna=_fake_planet(0.0),
            ascendant=0.0,
        )

    def test_returns_dict(self):
        bala = compute_harsha_bala(self.chart, 2451545.0)
        self.assertIsInstance(bala, dict)

    def test_no_ketu(self):
        bala = compute_harsha_bala(self.chart, 2451545.0)
        self.assertNotIn(Graha.KETU, bala)

    def test_all_planets_have_scores(self):
        bala = compute_harsha_bala(self.chart, 2451545.0)
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                   Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            self.assertIn(g, bala)

    def test_mercury_in_lagna_gets_house_bonus(self):
        planets = {}
        for g in Graha:
            planets[g] = _fake_planet(0.0)
        planets[Graha.MERCURY] = _fake_planet(0.0)  # 1st house = lagna
        chart = ChartData(
            birth_date=datetime(2000, 1, 1), julian_day=2451545.0,
            latitude=0.0, longitude=0.0, timezone="UTC",
            ayanamsa_name="lahiri", ayanamsa_value=23.5,
            planets={g: planets.get(g, _fake_planet(0.0)) for g in Graha},
            lagna=_fake_planet(0.0), ascendant=0.0,
        )
        bala = compute_harsha_bala(chart, 2451545.0)
        self.assertGreaterEqual(bala[Graha.MERCURY], 5)


class TestPatyayiniDasa(unittest.TestCase):

    def test_returns_list(self):
        planets = {g: _fake_planet(float(i) * 10) for i, g in
                   enumerate([Graha.SUN, Graha.MOON, Graha.MARS,
                              Graha.MERCURY, Graha.JUPITER, Graha.VENUS,
                              Graha.SATURN])}
        periods = compute_patyayini_dasa(planets, 0.0, 2451545.0)
        self.assertIsInstance(periods, list)

    def test_seven_periods(self):
        planets = {g: _fake_planet(float(i) * 10) for i, g in
                   enumerate([Graha.SUN, Graha.MOON, Graha.MARS,
                              Graha.MERCURY, Graha.JUPITER, Graha.VENUS,
                              Graha.SATURN])}
        periods = compute_patyayini_dasa(planets, 0.0, 2451545.0)
        self.assertEqual(len(periods), 7)

    def test_periods_cover_one_year(self):
        planets = {g: _fake_planet(float(i) * 10) for i, g in
                   enumerate([Graha.SUN, Graha.MOON, Graha.MARS,
                              Graha.MERCURY, Graha.JUPITER, Graha.VENUS,
                              Graha.SATURN])}
        periods = compute_patyayini_dasa(planets, 0.0, 2451545.0)
        total_days = sum(p.end_jd - p.start_jd for p in periods)
        self.assertAlmostEqual(total_days, 365.2425, delta=1.0)

    def test_periods_have_dasaperiod_type(self):
        planets = {g: _fake_planet(float(i) * 10) for i, g in
                   enumerate([Graha.SUN, Graha.MOON, Graha.MARS,
                              Graha.MERCURY, Graha.JUPITER, Graha.VENUS,
                              Graha.SATURN])}
        periods = compute_patyayini_dasa(planets, 0.0, 2451545.0)
        for p in periods:
            self.assertIsInstance(p, object)
            self.assertTrue(hasattr(p, 'lord_name'))
            self.assertTrue(hasattr(p, 'start_jd'))
            self.assertTrue(hasattr(p, 'end_jd'))


class TestMuddaDasa(unittest.TestCase):

    def test_returns_nine_periods(self):
        periods = compute_mudda_dasa(0.0, 0, 2451545.0)
        self.assertEqual(len(periods), 9)

    def test_total_days_is_360(self):
        periods = compute_mudda_dasa(0.0, 0, 2451545.0)
        total = sum(p.end_jd - p.start_jd for p in periods)
        self.assertAlmostEqual(total, 360.0, delta=1.0)

    def test_first_dasa_based_on_natal_moon(self):
        # Moon at 0° → nakshatra lord is Ketu → first lord is Ketu
        periods = compute_mudda_dasa(0.0, 0, 2451545.0)
        self.assertEqual(periods[0].lord_name, "Ke")

    def test_mudda_order_is_correct(self):
        names = [g.short_name for g in _MUDDA_ORDER]
        self.assertEqual(names, ["Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me", "Ke", "Ve"])

    def test_dasa_days_summary(self):
        expected = {
            "Su": 18, "Mo": 30, "Ma": 21, "Ra": 54,
            "Ju": 48, "Sa": 57, "Me": 51, "Ke": 21, "Ve": 60,
        }
        self.assertEqual(
            {g.short_name: v for g, v in _MUDDA_DAYS.items()},
            expected,
        )

    def test_progressed_years_change_first_dasa(self):
        p0 = compute_mudda_dasa(0.0, 0, 2451545.0)
        p1 = compute_mudda_dasa(0.0, 1, 2451545.0)
        self.assertNotEqual(p0[0].lord_name, p1[0].lord_name)

    def test_fraction_remaining_shortens_first_period(self):
        # Moon very early in nakshatra → almost full period
        early = compute_mudda_dasa(0.1, 0, 2451545.0)
        # Moon very late in nakshatra → short first period
        late = compute_mudda_dasa(13.0, 0, 2451545.0)
        self.assertGreater(
            early[0].end_jd - early[0].start_jd,
            late[0].end_jd - late[0].start_jd,
        )


if __name__ == "__main__":
    unittest.main()
