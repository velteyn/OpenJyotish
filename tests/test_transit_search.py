"""Tests for transit search — query-driven date search over conditions."""
from datetime import date, timedelta

import pytest

from jhora.calc.drishti import aspects_from
from jhora.calc.gochara import saturn_phase_timeline
from jhora.calc.transit_search import (
    SearchCondition,
    search_transits,
)
from jhora.charts.chart import ChartBuilder
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha


@pytest.fixture(scope="module")
def chart():
    # Jalkot reference chart.
    builder = ChartBuilder()
    return builder.build(2001, 2, 24, 6 + 11 / 60.0, 18.6333, 77.2,
                         tz="+0530")


def _moon_sign(chart):
    return int(chart.planets[Graha.MOON].longitude // 30) % 12


class TestHouseSearch:
    def test_saturn_houses_match_sade_sati_phases(self, chart):
        """Union of Saturn in 12/1/2 from Moon covers the Sade-Sati span."""
        moon = _moon_sign(chart)
        start, end = date(2020, 1, 1), date(2032, 1, 1)
        phases = [p for p in saturn_phase_timeline(moon, "lahiri",
                                                   start, end)
                  if p.kind == "Sade Sati"]
        assert phases, "expected a Sade-Sati phase in window"
        lo = min(p.start for p in phases)
        hi = max(p.end for p in phases)
        found_lo, found_hi = end, start
        for house in (12, 1, 2):
            res = search_transits(
                chart, SearchCondition(kind="house", planet=Graha.SATURN,
                                       house=house, basis="moon"),
                start, end)
            assert res.step_days == 1 and res.boundaries_refined
            for iv in res.intervals:
                found_lo = min(found_lo, iv.start)
                found_hi = max(found_hi, iv.end)
        assert found_lo <= lo + timedelta(days=3)
        assert found_hi >= hi - timedelta(days=3)

    def test_step_note_present(self, chart):
        res = search_transits(
            chart, SearchCondition(kind="house", planet=Graha.SUN,
                                   house=1, basis="lagna"),
            date(2025, 1, 1), date(2025, 2, 1))
        assert "Daily sweep" in res.note


class TestAspectSearch:
    def test_jupiter_aspects_moon_reference(self, chart):
        """Sample inside/outside dates against the day-by-day reference."""
        from jhora.calc.gochara import _GRAHA_TO_SE
        moon = _moon_sign(chart)
        start, end = date(2025, 1, 1), date(2026, 6, 1)
        res = search_transits(
            chart, SearchCondition(kind="aspect", planet=Graha.JUPITER,
                                   target=Graha.MOON),
            start, end)
        assert res.intervals, "expected Jupiter-Moon aspects in window"
        se = SweEngine()
        checked_in, checked_out = 0, 0

        def sign_on(day):
            return int(se.calc_planet(
                _GRAHA_TO_SE[Graha.JUPITER],
                se.julday(day.year, day.month, day.day, 12.0)
            ).longitude // 30) % 12

        def aspects(sign):
            return any(a.target_sign_index == moon
                       for a in aspects_from(Graha.JUPITER, sign))

        for iv in res.intervals:
            # Strict interior only: refined edges are day-approximations
            # by design (spec: boundaries refined to the day).
            day = iv.start + timedelta(days=2)
            while day <= iv.end - timedelta(days=2) and checked_in < 6:
                assert aspects(sign_on(day)), day
                checked_in += 1
                day += timedelta(days=7)
        day = start + timedelta(days=2)
        while day <= end - timedelta(days=2) and checked_out < 6:
            inside = any(iv.start + timedelta(days=2) <= day
                         <= iv.end - timedelta(days=2)
                         for iv in res.intervals)
            if not inside:
                assert not aspects(sign_on(day)), day
                checked_out += 1
            day += timedelta(days=7)
        assert checked_in and checked_out


class TestIngressSearch:
    def test_jupiter_ingresses_day_exact(self, chart):
        from jhora.calc.gochara import _GRAHA_TO_SE
        se = SweEngine()
        se_id = _GRAHA_TO_SE[Graha.JUPITER]
        start, end = date(2025, 1, 1), date(2027, 1, 1)
        res = search_transits(
            chart, SearchCondition(kind="ingress", planet=Graha.JUPITER),
            start, end)
        assert len(res.intervals) >= 2
        for iv in res.intervals:
            assert iv.start == iv.end  # ingress is a single day
            day = iv.start
            prev_sign = int(se.calc_planet(
                se_id, se.julday(day.year, day.month, day.day, 0.0) - 1.0
            ).longitude // 30) % 12
            new_sign = int(se.calc_planet(
                se_id, se.julday(day.year, day.month, day.day, 0.0) + 1.0
            ).longitude // 30) % 12
            assert prev_sign != new_sign, f"no crossing at {day}"
            assert iv.label.endswith(
                ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius",
                 "Pisces"][new_sign])


class TestEdgeCases:
    def test_empty_result_keeps_note(self, chart):
        res = search_transits(
            chart, SearchCondition(kind="house", planet=Graha.SUN,
                                   house=1, basis="moon"),
            date(2025, 6, 1), date(2025, 6, 1))
        assert res.intervals == [] or all(
            iv.start <= iv.end for iv in res.intervals)
        assert "Daily sweep" in res.note

    def test_reversed_window_rejected(self, chart):
        with pytest.raises(ValueError):
            search_transits(
                chart, SearchCondition(kind="house"),
                date(2026, 1, 1), date(2025, 1, 1))

    def test_window_cap_rejected(self, chart):
        with pytest.raises(ValueError):
            search_transits(
                chart, SearchCondition(kind="house"),
                date(2000, 1, 1), date(2040, 1, 1))

    def test_bad_house_rejected(self, chart):
        with pytest.raises(ValueError):
            search_transits(
                chart, SearchCondition(kind="house", house=13),
                date(2025, 1, 1), date(2025, 2, 1))

    def test_nodes_rejected(self, chart):
        with pytest.raises(ValueError):
            search_transits(
                chart, SearchCondition(kind="house", planet=Graha.RAHU),
                date(2025, 1, 1), date(2025, 2, 1))
