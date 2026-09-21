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


import pytest

from jhora.calc.tajaka import (
    SOLAR_YEAR_DAYS,
    TajakaLevel,
    build_tajaka_level_chart,
    level_offset_days,
)
from jhora.charts.chart import ChartBuilder


class TestTajakaLevels:
    def test_periods_per_year(self):
        assert [lvl.periods_per_year for lvl in TajakaLevel] == [
            1, 12, 144, 1728, 20736, 248832,
        ]

    def test_durations_are_duodecimal(self):
        assert TajakaLevel.ANNUAL.days == pytest.approx(SOLAR_YEAR_DAYS)
        assert TajakaLevel.MONTHLY.days == pytest.approx(SOLAR_YEAR_DAYS / 12)
        assert TajakaLevel.TWO_AND_HALF_DAY.days == pytest.approx(SOLAR_YEAR_DAYS / 144)
        assert TajakaLevel.FIVE_HOUR.days == pytest.approx(SOLAR_YEAR_DAYS / 1728)
        assert TajakaLevel.TWENTY_FIVE_MIN.days == pytest.approx(SOLAR_YEAR_DAYS / 20736)
        assert TajakaLevel.TWO_MIN.days == pytest.approx(SOLAR_YEAR_DAYS / 248832)

    def test_levels_nest_by_twelve(self):
        levels = list(TajakaLevel)
        for coarse, fine in zip(levels, levels[1:]):
            assert fine.days * 12 == pytest.approx(coarse.days)

    def test_index_one_is_the_anchor(self):
        for lvl in TajakaLevel:
            assert level_offset_days(lvl, 1) == 0.0

    def test_offsets_are_uniform(self):
        step = (level_offset_days(TajakaLevel.MONTHLY, 3)
                - level_offset_days(TajakaLevel.MONTHLY, 2))
        assert step == pytest.approx(TajakaLevel.MONTHLY.days)

    def test_invalid_index_rejected(self):
        for bad in (0, -1, 13):
            with pytest.raises(ValueError):
                level_offset_days(TajakaLevel.MONTHLY, bad)
        with pytest.raises(ValueError):
            level_offset_days(TajakaLevel.ANNUAL, 2)


def _natal_chart():
    cb = ChartBuilder()
    cb.swe.set_sidereal_mode("lahiri")
    natal = cb.build(
        year=1970, month=4, day=4, hour=23.3,
        lat=13.08, lon=80.27, tz="-5.5", ayanamsa="lahiri",
    )
    return cb, natal


class TestLevelCharts:
    def test_index_one_equals_the_anchor(self):
        cb, natal = _natal_chart()
        t = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.MONTHLY, 1)
        assert t.moment_jd == pytest.approx(t.anchor_jd)
        assert t.anchor_jd == pytest.approx(t.varsha_pravesh_jd)

    def test_annual_index_one_is_the_solar_return(self):
        cb, natal = _natal_chart()
        t = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.ANNUAL, 1)
        assert t.level == TajakaLevel.ANNUAL
        assert t.moment_jd == pytest.approx(t.anchor_jd)

    def test_offsets_are_uniform(self):
        cb, natal = _natal_chart()
        a = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.MONTHLY, 2)
        b = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.MONTHLY, 3)
        assert b.moment_jd - a.moment_jd == pytest.approx(TajakaLevel.MONTHLY.days)

    def test_invalid_index_raises(self):
        cb, natal = _natal_chart()
        with pytest.raises(ValueError):
            build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.MONTHLY, 13)

    def test_sunrise_variant(self):
        cb, natal = _natal_chart()
        exact = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                         TajakaLevel.MONTHLY, 3)
        sr = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                      TajakaLevel.MONTHLY, 3, sunrise=True)
        assert sr.sunrise
        assert abs(sr.moment_jd - exact.moment_jd) > 1e-3
        assert abs(sr.moment_jd - exact.moment_jd) < 1.0

    def test_deterministic(self):
        cb, natal = _natal_chart()
        a = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.TWO_AND_HALF_DAY, 4)
        b = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.TWO_AND_HALF_DAY, 4)
        assert a.moment_jd == b.moment_jd
        assert a.chart.ascendant == b.chart.ascendant


class TestMuddaSeedOptions:
    def test_default_is_natal_moon_seed(self):
        assert compute_mudda_dasa(0.0, 0, 2451545.0)[0].lord_name == "Ke"
        assert compute_mudda_dasa(0.0, 1, 2451545.0)[0].lord_name == "Ve"

    def test_seed_longitude_selects_another_seed(self):
        natal_seed = compute_mudda_dasa(0.0, 0, 2451545.0)
        annual_seed = compute_mudda_dasa(0.0, 0, 2451545.0, seed_longitude=100.0)
        assert natal_seed[0].lord_name != annual_seed[0].lord_name

    def test_progress_seed_false_keeps_the_seed(self):
        p0 = compute_mudda_dasa(0.0, 0, 2451545.0, progress_seed=False)
        p5 = compute_mudda_dasa(0.0, 5, 2451545.0, progress_seed=False)
        assert p0[0].lord_name == p5[0].lord_name == "Ke"


class TestLevelApparatus:
    def test_level_chart_carries_the_tajaka_apparatus(self):
        cb, natal = _natal_chart()
        t = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.MONTHLY, 2)
        assert t.harsha_bala
        assert len(t.patyayini_dasa) > 0
        assert len(t.mudda_dasa) == 9
        # periods begin at the level chart's own moment
        assert t.patyayini_dasa[0].start_jd == pytest.approx(t.moment_jd)
        assert t.mudda_dasa[0].start_jd == pytest.approx(t.moment_jd)

    def test_anchor_and_moment_reported(self):
        cb, natal = _natal_chart()
        t = build_tajaka_level_chart(cb.swe, cb, natal, 2026,
                                     TajakaLevel.FIVE_HOUR, 5)
        assert t.anchor_jd is not None and t.moment_jd is not None
        assert t.moment_jd > t.anchor_jd
        assert t.level == TajakaLevel.FIVE_HOUR
        assert t.index == 5
