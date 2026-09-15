"""Tests for Karaka, Moola and Shoola dasas.

Mahadasha sequences below were hand-derived from the classical rules
(see module docstrings) for the 1990 Bangalore fixture and checked
twice; the ref_chart cases assert structural invariants instead.
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.karaka_dasa import KarakaDasa
from jhora.dasas.moola import MoolaDasa
from jhora.dasas.shoola import ShoolaDasa
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


def _chart_1990():
    b = ChartBuilder()
    return b.build(1990, 1, 15, 17.5, 12.9716, 77.5946, tz="-5.5")


def _dict(cd):
    return {"planets": {g: {"longitude": p.longitude}
                        for g, p in cd.planets.items()},
            "lagna_lon": cd.ascendant}


def _lords(periods):
    return [p.lord_name for p in periods]


def _durs(periods):
    return [p.duration_years for p in periods]


class TestShoola:
    def test_sequence_and_durations(self):
        # Lagna trines Ge(Ke)/Li(-)/Aq(-): counts 1/0/0 → start Gemini.
        # Third group from Aquarius runs Aq,Pi,Ar,Ta (mod-12 stepping).
        cd = _chart_1990()
        periods = ShoolaDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn",
            "Aquarius", "Pisces", "Aries", "Taurus"]
        assert _durs(periods) == [9, 7, 8, 9, 7, 8, 9, 7, 8, 9, 7, 8]
        assert sum(_durs(periods)) == 96

    def test_contiguous_from_birth(self):
        cd = _chart_1990()
        periods = ShoolaDasa().compute(cd.julian_day, _dict(cd))
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd

    def test_antardasas_sum_to_md(self):
        cd = _chart_1990()
        periods = ShoolaDasa().compute(cd.julian_day, _dict(cd))
        for md in periods[:3]:
            total = sum(ad.duration_years for ad in md.sub_periods)
            assert total == pytest.approx(md.duration_years)
        assert md.sub_periods[0].lord_name == md.lord_name


class TestMoola:
    def test_starts_at_strongest_planet_sign(self):
        # Su/Ve/Ra tie at 320; strict-first keeps Sun → Capricorn.
        cd = _chart_1990()
        periods = MoolaDasa().compute(cd.julian_day, _dict(cd))
        assert periods[0].lord_name == "Capricorn"
        assert _lords(periods) == [
            "Capricorn", "Aquarius", "Pisces", "Aries",
            "Taurus", "Gemini", "Cancer", "Leo",
            "Virgo", "Libra", "Scorpio", "Sagittarius"]

    def test_twelve_year_cycle(self):
        cd = _chart_1990()
        periods = MoolaDasa().compute(cd.julian_day, _dict(cd))
        assert _durs(periods) == [12] * 12
        assert sum(_durs(periods)) == 144


class TestKaraka:
    def test_dara_sequence_and_durations(self):
        # In-sign degrees: Ma 26.19 > Mo 23.78 > Sa 23.59 > Ra 19.98 >
        # Me 17.62 > Ju 9.64 > Ve 6.96 > Su 1.36 → Dara is Sun (Capricorn).
        # Scorpio resolves to Ketu (Rao own-sign exception: Mars in
        # Scorpio, Ketu elsewhere), so its MD runs 5 years.
        cd = _chart_1990()
        periods = KarakaDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Capricorn", "Aquarius", "Pisces", "Aries",
            "Taurus", "Gemini", "Cancer", "Leo",
            "Virgo", "Libra", "Scorpio", "Sagittarius"]
        assert _durs(periods) == [2, 11, 10, 8, 5, 7, 11, 6, 10, 4, 5, 7]
        assert sum(_durs(periods)) == 86

    def test_putra_starts_at_jupiters_sign(self):
        # Putra Karaka is Jupiter (6th) in Gemini.
        cd = _chart_1990()
        opts = DasaOptions(karaka_role="Putra")
        periods = KarakaDasa(opts).compute(cd.julian_day, _dict(cd), opts)
        assert periods[0].lord_name == "Gemini"

    def test_bad_role_rejected(self):
        cd = _chart_1990()
        opts = DasaOptions(karaka_role="Wealth")
        try:
            KarakaDasa(opts).compute(cd.julian_day, _dict(cd), opts)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")

    def test_antardasa_parity_and_sums(self):
        cd = _chart_1990()
        periods = KarakaDasa().compute(cd.julian_day, _dict(cd))
        md = periods[0]  # Capricorn (even) → ADs run backward
        assert md.sub_periods[0].lord_name == "Capricorn"
        assert md.sub_periods[1].lord_name == "Sagittarius"
        total = sum(ad.duration_years for ad in md.sub_periods)
        assert total == pytest.approx(md.duration_years)


class TestRefChartStructural:
    """Second chart (1970 Chennai): invariants, not hardcoded sequences."""

    def test_shoola_total_in_range_and_contiguous(self, ref_chart):
        cd, d = ref_chart, _dict(ref_chart)
        periods = ShoolaDasa().compute(cd.julian_day, d)
        assert 93 <= sum(_durs(periods)) <= 99
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd

    def test_moola_always_144(self, ref_chart):
        cd, d = ref_chart, _dict(ref_chart)
        periods = MoolaDasa().compute(cd.julian_day, d)
        assert sum(_durs(periods)) == 144

    def test_karaka_matches_cycle_totals(self, ref_chart):
        from jhora.dasas.jaimini_common import (
            chara_cycle_years, normalize_planets, planet_signs)
        from jhora.calc.karaka import compute_chara_karakas, karaka_dict
        cd, d = ref_chart, _dict(ref_chart)
        periods = KarakaDasa().compute(cd.julian_day, d)
        planets = normalize_planets(d["planets"])
        assert sum(_durs(periods)) == sum(
            chara_cycle_years(planet_signs(planets)))
        full = {g: {"longitude": lon} for g, lon in planets.items()}
        dk = karaka_dict(compute_chara_karakas(full))["DK"].graha
        assert periods[0].lord_name == Rasi(
            planet_signs(planets)[dk]).full_name
