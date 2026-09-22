"""Tests for Moola dasa and its Tara variant.

The year correction is checked against the known periods for the 1970-04-04
23:18 Chennai chart. The within-family ordering is a documented approximation
- see the module docstring - so these tests assert the validated parts and
the shape of the rest, never a fitted full order.
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.moola import (
    DEBILITATION_SIGN,
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

    def test_groups_follow_kendra_panaphara_apoklima(self):
        # The validated property: planets are emitted in contiguous family
        # blocks (same (sign - ak_sign) % 3), in the family order the engine
        # documents. Membership and block structure are what the reference
        # pins; the intra-family lead is the documented approximation.
        from jhora.calc.karaka import compute_chara_karakas
        _cd, ch = _chart_dict()
        ak = compute_chara_karakas(
            {g: {"longitude": v["longitude"]} for g, v in ch["planets"].items()}
        )[0].graha
        ak_sign = int(ch["planets"][ak]["longitude"] // 30) % 12
        periods = MoolaDasa().compute(0.0, ch, DasaOptions())
        families = []
        for p in periods:
            sign = int(ch["planets"][Graha(p.lord_index)]["longitude"] // 30) % 12
            families.append((sign - ak_sign) % 3)
        # Each family must be a single contiguous run.
        runs = [families[0]]
        for f in families[1:]:
            if f != runs[-1]:
                runs.append(f)
        assert len(runs) == len(set(runs)), f"family not contiguous: {families}"
        assert runs == [1, 0, 2]

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


class TestTaraVariant:
    def test_tara_differs_for_moolatrikona_planet(self):
        # Mercury/Venus in moolatrikona: Moola gives correction 12, Tara 0, so
        # their periods differ by 12 years.
        _cd, ch = _chart_dict()
        moola = MoolaDasa().compute(0.0, ch, DasaOptions())
        tara = MoolaDasa().compute(0.0, ch, DasaOptions(tara_variant=True))
        m_by = {p.lord_index: p.duration_years for p in moola}
        t_by = {p.lord_index: p.duration_years for p in tara}
        assert m_by != t_by

    def test_tara_md_order_matches_moola(self):
        # The variant changes years, not the sequence.
        _cd, ch = _chart_dict()
        moola = MoolaDasa().compute(0.0, ch, DasaOptions())
        tara = MoolaDasa().compute(0.0, ch, DasaOptions(tara_variant=True))
        assert [p.lord_index for p in moola] == [p.lord_index for p in tara]


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
