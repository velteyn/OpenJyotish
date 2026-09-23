"""Tests for the Sade Sati / Kantaka / Ashtama timeline (gochara)."""

from datetime import date

import pytest
from typer.testing import CliRunner

from jhora.cli.main import app
from jhora.calc.gochara import (
    current_phase,
    next_sade_sati_start,
    sade_sati_status,
    sade_sati_timeline,
    saturn_phase_timeline,
    saturn_sidereal_rasi,
)
from jhora.ephemeris.swe import SweEngine

runner = CliRunner()
JALKOT = "2001-02-24 06:11:00 +0530 18.6333 77.2"


def _jd(y, m, d):
    return SweEngine().julday(y, m, d, 0.0)


class TestSaturnAnchor:
    def test_sidereal_aquarius_mid_2024(self):
        assert saturn_sidereal_rasi(_jd(2024, 6, 1)) == 10

    def test_sidereal_pisces_mid_2025(self):
        assert saturn_sidereal_rasi(_jd(2025, 6, 1)) == 11


class TestSadeSatiStructure:
    def test_moon_aries_covers_mid_2025_as_12th(self):
        ph = saturn_phase_timeline(0, "lahiri",
                                   date(2024, 1, 1), date(2026, 12, 31))
        twelfth = [p for p in ph if p.phase == "12th from Moon"]
        assert len(twelfth) == 1
        assert twelfth[0].start <= date(2025, 6, 1) <= twelfth[0].end
        assert date(2025, 2, 1) <= twelfth[0].start <= date(2025, 5, 15)

    def test_phase_order_and_spans(self):
        ph = sade_sati_timeline(0, "lahiri")
        sade = [p for p in ph if p.kind == "Sade Sati"]
        order = {"12th from Moon": 0, "1st from Moon (peak)": 1,
                 "2nd from Moon": 2}
        first = {}
        for p in sade:
            first.setdefault(p.phase, p.start)
        assert ([order[k] for k in first] ==
                sorted(order[k] for k in first))
        totals = {}
        for p in sade:
            totals[p.phase] = totals.get(p.phase, 0) + \
                (p.end - p.start).days
        for days in totals.values():
            assert 1.5 * 365 < days < 4 * 365
        assert 6.5 * 365 < sum(totals.values()) < 9 * 365

    def test_midpoint_matches_point_status(self):
        ph = sade_sati_timeline(5, "lahiri")  # Moon in Leo
        for p in [x for x in ph if x.kind == "Sade Sati"]:
            assert sade_sati_status(5, p.sign) == p.phase

    def test_small_panoti_signs(self):
        ph = saturn_phase_timeline(0, "lahiri",
                                   date(2000, 1, 1), date(2019, 12, 31))
        kantaka = [p for p in ph if p.kind == "Kantaka Shani"]
        ashtama = [p for p in ph if p.kind == "Ashtama Shani"]
        assert kantaka and all(p.sign == 3 for p in kantaka)
        assert ashtama and all(p.sign == 7 for p in ashtama)

    def test_empty_window(self):
        assert saturn_phase_timeline(
            0, "lahiri", date(2025, 1, 1), date(2025, 1, 1)) == []


class TestHelpers:
    def test_current_phase(self):
        ph = saturn_phase_timeline(0, "lahiri",
                                   date(2018, 1, 1), date(2030, 12, 31))
        cur = current_phase(ph, date(2026, 1, 1))
        assert cur is not None and cur.phase == "12th from Moon"
        assert current_phase(ph, date(2019, 1, 1)) is None
        assert current_phase([], date(2026, 1, 1)) is None

    def test_next_sade_sati_start(self):
        # Moon in Aquarius: Sade Sati opens with Saturn's Capricorn ingress.
        ph = saturn_phase_timeline(10, "lahiri",
                                   date(2018, 1, 1), date(2030, 12, 31))
        assert next_sade_sati_start(ph, date(2019, 6, 1)) == date(2020, 1, 24)
        assert next_sade_sati_start(ph, date(2028, 6, 1)) is None


class TestSadeSatiCli:
    def test_sade_sati_command(self):
        result = runner.invoke(app, ["sade-sati", JALKOT])
        assert result.exit_code == 0, result.output
        assert "Sade Sati" in result.output
        assert "← now" in result.output or "Now" in result.output


class TestNodeModeTransit:
    def test_transit_nodes_honor_chart_mode(self):
        import swisseph as _swe
        from jhora.charts.chart import ChartBuilder
        from jhora.calc.gochara import compute_transits
        from jhora.ephemeris.swe import SweEngine
        kw = dict(year=2001, month=2, day=24, hour=6 + 11 / 60,
                  lat=18.63, lon=77.2, tz="+0530", ayanamsa="lahiri")
        mean_cd = ChartBuilder().build(**kw)
        true_cd = ChartBuilder().build(**kw, nodes="true")
        se = SweEngine()
        jd = se.julday(2026, 5, 1, 12.0)
        tr_mean = compute_transits(mean_cd, jd)
        tr_true = compute_transits(true_cd, jd)
        assert tr_mean.transit_rahu_rasi == \
            int(se.calc_planet(_swe.MEAN_NODE, jd).longitude // 30) % 12
        se.set_use_true_nodes(True)
        assert tr_true.transit_rahu_rasi == \
            int(se.calc_planet(_swe.TRUE_NODE, jd).longitude // 30) % 12
        assert tr_true.transit_ketu_rasi == \
            (tr_true.transit_rahu_rasi + 6) % 12
