"""Tests for Moola dasa and its Tara variant.

The period formula and the mahadasa order are checked against the known
1970-04-04 23:18 Chennai chart (order: Sun, Moon, Rahu, Ketu, Mars, Venus,
Mercury, Saturn, Jupiter; years 1 8 6 4 5 14 12 10 14).
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.moola import (
    DEBILITATION_SIGN,
    EXALTATION_SIGN,
    MOOLATRIKONA,
    MoolaDasa,
    moola_correction,
    moola_years,
)
from jhora.types.graha import Graha


def _chart_dict():
    cb = ChartBuilder()
    cb.swe.set_sidereal_mode("lahiri")
    cd = cb.build(year=1970, month=4, day=4, hour=23.3,
                  lat=13.08, lon=80.27, tz="-5.5", ayanamsa="lahiri")
    return cd, {
        "planets": {g: {"longitude": p.longitude, "speed": p.speed}
                    for g, p in cd.planets.items()},
        "lagna_lon": cd.ascendant,
    }


# First-cycle years for the 1970 Chennai chart.
REFERENCE_YEARS = {
    Graha.SUN: 1, Graha.MOON: 8, Graha.RAHU: 6, Graha.KETU: 4,
    Graha.MARS: 5, Graha.VENUS: 14, Graha.MERCURY: 12,
    Graha.SATURN: 10, Graha.JUPITER: 14,
}

# Mahadasa order for the same chart.
REFERENCE_ORDER = [
    Graha.SUN, Graha.MOON, Graha.RAHU, Graha.KETU, Graha.MARS,
    Graha.VENUS, Graha.MERCURY, Graha.SATURN, Graha.JUPITER,
]


class TestCorrection:
    def test_ordinary_correction_is_distance_to_moolatrikona(self):
        # Sun in Pisces (11), moolatrikona Leo (4): (4-11)%12 = 5
        assert moola_correction(Graha.SUN, 11) == 5

    def test_in_moolatrikona_gives_twelve(self):
        for g, sign in MOOLATRIKONA.items():
            assert moola_correction(g, sign) == 12

    def test_tara_disables_the_moolatrikona_twelve(self):
        for g, sign in MOOLATRIKONA.items():
            assert moola_correction(g, sign,
                                    no_moolatrikona_correction=True) == 0

    def test_debilitated_reduces_by_one(self):
        # Saturn in Aries (0) is debilitated; moolatrikona Aquarius (10):
        # (10-0)%12 = 10, minus 1 = 9
        assert DEBILITATION_SIGN[Graha.SATURN] == 0
        assert moola_correction(Graha.SATURN, 0) == 9


class TestYears:
    def test_abs_clamp_never_negative(self):
        # Mercury in its moolatrikona: correction 12, Vimsottari 17 -> 5
        assert moola_years(Graha.MERCURY, MOOLATRIKONA[Graha.MERCURY]) == 5

    def test_reference_years_match_for_the_1970_chart(self):
        _cd, ch = _chart_dict()
        periods = MoolaDasa().compute(0.0, ch, DasaOptions())
        got = {p.lord_index: p.duration_years for p in periods}
        for g, years in REFERENCE_YEARS.items():
            assert got[g.value] == years, g.full_name


class TestSequence:
    def test_all_nine_planets_present_once(self):
        _cd, ch = _chart_dict()
        periods = MoolaDasa().compute(0.0, ch, DasaOptions())
        assert len(periods) == 9
        assert {p.lord_index for p in periods} == {g.value for g in Graha}

    def test_mahadasa_order_matches_reference(self):
        # The exact 1970 order. The cycle is anchored at the sign holding the
        # most bodies among the Lagna/Sun/Moon (Pisces: Sun and Moon), walks
        # the kendra jumps, and ranks signs by occupancy then planet dignity.
        _cd, ch = _chart_dict()
        periods = MoolaDasa().compute(0.0, ch, DasaOptions())
        assert [Graha(p.lord_index) for p in periods] == REFERENCE_ORDER

    def test_values_are_the_moola_corrections(self):
        _cd, ch = _chart_dict()
        periods = MoolaDasa().compute(0.0, ch, DasaOptions())
        assert [p.duration_years for p in periods] == \
               [REFERENCE_YEARS[g] for g in REFERENCE_ORDER]

    def test_antardasas_rotate_from_the_md_lord(self):
        _cd, ch = _chart_dict()
        periods = MoolaDasa().compute(0.0, ch, DasaOptions())
        md = periods[0]
        assert md.sub_periods
        assert md.sub_periods[0].lord_index == md.lord_index

    def test_deterministic(self):
        _cd, ch = _chart_dict()
        a = MoolaDasa().compute(0.0, ch, DasaOptions())
        b = MoolaDasa().compute(0.0, ch, DasaOptions())
        assert [(p.lord_name, p.end_jd) for p in a] == \
               [(p.lord_name, p.end_jd) for p in b]


class TestSyntheticOrders:
    """Extra oracle-verified sequences (all exercise the Scorpio/Aquarius
    co-lord path, which the 1970 fixture short-circuits)."""

    CASES = [
        (
            {0: 1, 1: 5, 2: 8, 3: 8, 4: 10, 5: 1, 6: 3, 7: 9, 8: 9, 9: 8},
            {1: 162.6184, 2: 257.1771, 3: 265.2721, 4: 323.2972, 5: 44.7271,
             6: 113.1922, 7: 283.2328, 8: 270.076, 9: 242.4217},
            ["Ketu", "Mars", "Moon", "Sun", "Saturn", "Rahu", "Venus",
             "Jupiter", "Mercury"],
        ),
        (
            {0: 4, 1: 1, 2: 7, 3: 0, 4: 10, 5: 7, 6: 10, 7: 5, 8: 3, 9: 6},
            {1: 37.5454, 2: 239.3974, 3: 27.8795, 4: 324.1541, 5: 239.9897,
             6: 315.4076, 7: 152.2896, 8: 100.2118, 9: 196.7235},
            ["Mercury", "Venus", "Jupiter", "Moon", "Sun", "Rahu", "Mars",
             "Ketu", "Saturn"],
        ),
        (
            {0: 4, 1: 4, 2: 7, 3: 2, 4: 10, 5: 11, 6: 11, 7: 9, 8: 4, 9: 0},
            {1: 145.4338, 2: 221.0653, 3: 73.8322, 4: 302.7205, 5: 356.7291,
             6: 346.6335, 7: 296.0168, 8: 132.7633, 9: 24.0765},
            ["Sun", "Rahu", "Mercury", "Moon", "Venus", "Jupiter", "Mars",
             "Saturn", "Ketu"],
        ),
    ]

    def test_orders(self):
        for signs, lon, expected in self.CASES:
            ch = {
                "planets": {
                    Graha(i - 1): {"longitude": lon[i]} for i in range(1, 10)
                },
                "lagna_lon": signs[0] * 30 + 15.0,
            }
            periods = MoolaDasa().compute(0.0, ch, DasaOptions())
            got = [p.lord_name for p in periods]
            assert got == expected, (signs, got)


class TestBaseSelectionSwitches:
    """The Lagna/Sun/Moon inclusion switches gate the base sign."""

    def test_default_uses_all_three_references(self):
        _cd, ch = _chart_dict()
        periods = MoolaDasa().compute(0.0, ch, DasaOptions())
        assert [p.lord_name for p in periods] == \
            [g.full_name for g in REFERENCE_ORDER]

    def test_disabling_sun_keeps_base_when_moon_shares_the_sign(self):
        # Sun and Moon are both in Pisces, so dropping the Sun from the
        # candidate set does not move the base.
        _cd, ch = _chart_dict()
        a = MoolaDasa().compute(0.0, ch, DasaOptions())
        b = MoolaDasa().compute(0.0, ch, DasaOptions(moola_use_sun=False))
        assert [p.lord_name for p in a] == [p.lord_name for p in b]

    def test_disabling_sun_and_moon_falls_back_to_lagna(self):
        # Lagna is Sagittarius (empty); the cycle then anchors there, which
        # pushes the Rahu/Ketu group to the end.
        _cd, ch = _chart_dict()
        periods = MoolaDasa().compute(
            0.0, ch, DasaOptions(moola_use_sun=False, moola_use_moon=False))
        assert [p.lord_name for p in periods] == \
            ["Sun", "Moon", "Mars", "Venus", "Mercury", "Saturn",
             "Jupiter", "Rahu", "Ketu"]


def _tara_chart(y, m, d, h, lat, lon, tz):
    cd = ChartBuilder().build(year=y, month=m, day=d, hour=h,
                              lat=lat, lon=lon, tz=tz,
                              ayanamsa="pushya_paksha")
    ch = {"planets": {g: {"longitude": p.longitude}
                      for g, p in cd.planets.items()},
          "lagna_lon": cd.ascendant}
    return cd, ch


class TestTara:
    """Tara dasa's two definitions, against captured reference orders.

    Parasara = Vimsottari sequence from the lord of the 9th sign from lagna;
    Rath = Moola sign-family walk from the lagna. Both use full Vimsottari
    years; the sesham is the Moon's nakshatra fraction.
    """

    PARASARA = [
        ((1970, 4, 4, 23.3, 13.08, 80.27, "-5.5"),
         ["Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
          "Ketu", "Venus"]),
        ((1990, 1, 15, 17.5, 12.9716, 77.5946, "+0530"),
         ["Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars",
          "Rahu", "Jupiter"]),
    ]
    RATH = [
        ((1970, 4, 4, 23.3, 13.08, 80.27, "-5.5"),
         ["Sun", "Moon", "Mars", "Venus", "Mercury", "Saturn", "Jupiter",
          "Rahu", "Ketu"]),
        ((1990, 1, 15, 17.5, 12.9716, 77.5946, "+0530"),
         ["Saturn", "Mercury", "Jupiter", "Venus", "Rahu", "Sun", "Ketu",
          "Moon", "Mars"]),
    ]

    def test_parasara_definition(self):
        for args, expected in self.PARASARA:
            cd, ch = _tara_chart(*args)
            periods = MoolaDasa().compute(
                cd.julian_day, ch, DasaOptions(tara_variant=True))
            assert [p.lord_name for p in periods] == expected

    def test_rath_definition_no_sesham_starts_at_birth(self):
        for args, expected in self.RATH:
            cd, ch = _tara_chart(*args)
            periods = MoolaDasa().compute(
                cd.julian_day, ch,
                DasaOptions(tara_variant=True, tara_definition="rath",
                            tara_use_sesham=False))
            assert [p.lord_name for p in periods] == expected
            assert periods[0].start_jd == cd.julian_day

    def test_years_are_full_vimsottari(self):
        cd, ch = _tara_chart(1990, 1, 15, 17.5, 12.9716, 77.5946, "+0530")
        periods = MoolaDasa().compute(
            cd.julian_day, ch, DasaOptions(tara_variant=True))
        assert {p.lord_index: p.duration_years for p in periods} == {
            g.value: g.vimsottari_years for g in Graha}

    def test_use_sesham_moves_the_start_before_birth(self):
        cd, ch = _tara_chart(1970, 4, 4, 23.3, 13.08, 80.27, "-5.5")
        with_s = MoolaDasa().compute(0.0, ch, DasaOptions(tara_variant=True))
        no_s = MoolaDasa().compute(
            0.0, ch, DasaOptions(tara_variant=True, tara_use_sesham=False))
        assert with_s[0].start_jd < no_s[0].start_jd


class TestNodeExaltation:
    """The nodes exalt in Gemini (Rahu) and Sagittarius (Ketu)."""

    def test_rahu_exalts_in_gemini(self):
        assert EXALTATION_SIGN[Graha.RAHU] == 2
        base = (MOOLATRIKONA[Graha.RAHU] - 2) % 12
        assert moola_correction(Graha.RAHU, 2) == base + 1

    def test_ketu_exalts_in_sagittarius(self):
        assert EXALTATION_SIGN[Graha.KETU] == 8
        base = (MOOLATRIKONA[Graha.KETU] - 8) % 12
        assert moola_correction(Graha.KETU, 8) == base + 1


class TestYearsZeroFallback:
    """A zero result takes the full Vimsottari period. Four planet/sign
    combinations hit it; without the guard they would get a zero-length
    period."""

    CASES = [
        (Graha.SUN, 10, 6.0),     # correction 6, Vimsottari 6
        (Graha.MOON, 3, 10.0),
        (Graha.MARS, 5, 7.0),
        (Graha.KETU, 0, 7.0),
    ]

    def test_zero_yields_full_period(self):
        for graha, sign, full in self.CASES:
            assert moola_years(graha, sign) == full

    def test_correction_equals_full_years_in_those_cases(self):
        for graha, sign, full in self.CASES:
            assert moola_correction(graha, sign) == full


class TestMoolaFormula:
    """The Moola length formula: remainder semantics plus the
    exaltation/debilitation adjustments."""

    # (graha, sign, expected years) for the reference chart placements.
    CASES = [
        (Graha.SUN, 11, 1), (Graha.MOON, 11, 8), (Graha.MARS, 0, 5),
        (Graha.MERCURY, 0, 12), (Graha.JUPITER, 6, 14), (Graha.VENUS, 0, 14),
        (Graha.SATURN, 0, 10), (Graha.RAHU, 10, 6), (Graha.KETU, 4, 4),
    ]

    def test_years_for_known_placements(self):
        for graha, sign, years in self.CASES:
            assert moola_years(graha, sign) == years, graha.full_name

    def test_debilitation_adjustment(self):
        # Saturn in Aries is debilitated: (10-0)%12 = 10, minus 1 = 9 -> 19-9=10
        from jhora.dasas.moola import DEBILITATION_SIGN
        assert DEBILITATION_SIGN[Graha.SATURN] == 0
        assert moola_correction(Graha.SATURN, 0) == 9
        assert moola_years(Graha.SATURN, 0) == 10
