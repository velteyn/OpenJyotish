"""Tests for Trikona and Varnada dasas.

Mahadasha sequences below were hand-derived from the classical rules
(see module docstrings) for the 1990 Bangalore fixture and checked
twice; the ref_chart cases assert structural invariants instead.
"""

import pytest

from jhora.charts.chart import ChartBuilder
from jhora.dasas.trikona import TrikonaDasa
from jhora.dasas.varnada import VarnadaDasa, _varnada_sign


def _chart_1990():
    b = ChartBuilder()
    return b.build(1990, 1, 15, 17.5, 12.9716, 77.5946, tz="-5.5")


def _dict(cd, extra=None):
    d = {"planets": {g: {"longitude": p.longitude}
                     for g, p in cd.planets.items()},
         "lagna_lon": cd.ascendant}
    if extra:
        d.update(extra)
    return d


def _dict_with_hora(cd):
    from jhora.calc.special_lagnas import hora_lagna
    hl = hora_lagna(cd)
    assert hl is not None
    return _dict(cd, {"hora_lagna_lon": hl})


def _lords(periods):
    return [p.lord_name for p in periods]


def _durs(periods):
    return [p.duration_years for p in periods]


class TestTrikona:
    def test_sequence_and_durations(self):
        # Strongest lagna trine is Gemini itself → forward from Gemini;
        # Chara-counted durations reproduce the tradition exactly.
        cd = _chart_1990()
        periods = TrikonaDasa().compute(cd.julian_day, _dict(cd))
        assert _lords(periods) == [
            "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn",
            "Aquarius", "Pisces", "Aries", "Taurus"]
        assert _durs(periods) == [6, 11, 7, 9, 3, 8, 6, 1, 1, 9, 7, 8]
        assert sum(_durs(periods)) == 76

    def test_contiguous_from_birth(self):
        cd = _chart_1990()
        periods = TrikonaDasa().compute(cd.julian_day, _dict(cd))
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd

    def test_antardasas_sum_to_md(self):
        cd = _chart_1990()
        periods = TrikonaDasa().compute(cd.julian_day, _dict(cd))
        for md in periods[:3]:
            total = sum(ad.duration_years for ad in md.sub_periods)
            assert total == pytest.approx(md.duration_years)
        assert md.sub_periods[0].lord_name == md.lord_name


class TestVarnada:
    def test_varnada_sign_fixture(self):
        # Gemini lagna (odd) + Hora Lagna Scorpio → Capricorn.
        from jhora.calc.special_lagnas import hora_lagna
        cd = _chart_1990()
        hl = hora_lagna(cd)
        assert hl is not None
        assert int(hl // 30) % 12 == 7  # Scorpio
        from jhora.types.graha import Graha
        assert _varnada_sign(cd.ascendant, hl,
                             cd.planets[Graha.SUN].longitude) == 9

    def test_sign_rule_branches(self):
        # Odd lagna adds, even lagna subtracts (pure function, no ephemeris).
        assert _varnada_sign(0.0, 30.0, 0.0) == 1  # Aries + Taurus → Taurus
        assert _varnada_sign(30.0, 30.0, 0.0) == 0  # Taurus − Taurus → Aries

    def test_sequence_and_durations(self):
        # Varnada Capricorn (even) → backward; footed counts minus one
        # (cross-checked against Pythe tradition); Scorpio runs 8 via Ketu
        # (Rao own-sign exception: Mars in Scorpio, Ketu elsewhere).
        cd = _chart_1990()
        periods = VarnadaDasa().compute(cd.julian_day, _dict_with_hora(cd))
        assert _lords(periods) == [
            "Capricorn", "Sagittarius", "Scorpio", "Libra",
            "Virgo", "Leo", "Cancer", "Gemini",
            "Taurus", "Aries", "Pisces", "Aquarius"]
        assert _durs(periods) == [1, 6, 8, 3, 9, 7, 11, 6, 8, 7, 9, 1]

    def test_contiguous_from_birth(self):
        cd = _chart_1990()
        periods = VarnadaDasa().compute(cd.julian_day, _dict_with_hora(cd))
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd

    def test_antardasas_sum_to_md(self):
        cd = _chart_1990()
        periods = VarnadaDasa().compute(cd.julian_day, _dict_with_hora(cd))
        for md in periods[:3]:
            total = sum(ad.duration_years for ad in md.sub_periods)
            assert total == pytest.approx(md.duration_years)
        assert md.sub_periods[0].lord_name == md.lord_name

    def test_sun_fallback_completes(self):
        # Without hora_lagna_lon the Sun's sign seeds VL; still 12 MDs.
        cd = _chart_1990()
        periods = VarnadaDasa().compute(cd.julian_day, _dict(cd))
        assert len(periods) == 12
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd


class TestVarnadaSurfaces:
    """Every surface chart path carries the true Hora Lagna (Capricorn)."""

    def _engine_first(self, d):
        from jhora.charts.chart import ChartBuilder
        cd = _chart_1990()
        return VarnadaDasa().compute(cd.julian_day, d)[0].lord_name

    def test_cli_dict(self):
        from jhora.cli.main import _chart_to_dict
        assert self._engine_first(_chart_to_dict(_chart_1990())) == "Capricorn"

    def test_tui_dict(self):
        from jhora.tui.main import _chart_to_dict
        assert self._engine_first(_chart_to_dict(_chart_1990())) == "Capricorn"

    def test_gui_dict(self):
        from jhora.ui.main_window import MainWindow
        assert self._engine_first(
            MainWindow._dasa_chart_dict(_chart_1990())) == "Capricorn"

    def test_ai_json_matches_engine(self):
        from datetime import datetime
        from jhora.ai.json_export import chart_to_json
        cd = _chart_1990()
        result = chart_to_json(cd)
        now = datetime.now()
        from jhora.cli.main import _chart_to_dict
        for p in VarnadaDasa().compute(
                cd.julian_day, _chart_to_dict(cd)):
            if p.start_date <= now <= p.end_date:
                assert result["dasa"]["systems"]["varnada"][
                    "current_mahadasha_lord"] == p.lord_name
                break
        else:
            raise AssertionError("no current Varnada MD found")


class TestRefChartStructural:
    """Second chart (1970 Chennai): invariants, not hardcoded sequences."""

    def test_trikona_matches_cycle_totals(self, ref_chart):
        from jhora.dasas.jaimini_common import (
            chara_cycle_years, normalize_planets, planet_signs)
        cd, d = ref_chart, _dict(ref_chart)
        periods = TrikonaDasa().compute(cd.julian_day, d)
        planets = normalize_planets(d["planets"])
        assert sum(_durs(periods)) == sum(
            chara_cycle_years(planet_signs(planets)))
        assert len(set(_lords(periods))) == 12
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd

    def test_varnada_contiguous(self, ref_chart):
        from jhora.calc.special_lagnas import hora_lagna
        cd = ref_chart
        hl = hora_lagna(cd)
        d = _dict(cd, {"hora_lagna_lon": hl} if hl is not None else None)
        periods = VarnadaDasa().compute(cd.julian_day, d)
        assert len(periods) == 12
        assert periods[0].start_jd == cd.julian_day
        for a, b in zip(periods, periods[1:]):
            assert a.end_jd == b.start_jd
