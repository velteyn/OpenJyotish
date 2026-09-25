"""Tests for Asta-Udaya — pure span logic + real-scan invariants."""

from datetime import date

from jhora.calc.asta_udaya import asta_periods, spans_from_states
from jhora.types.graha import Graha


class TestSpans:
    def test_basic(self):
        ds = [date(2026, 1, d) for d in range(1, 7)]
        assert spans_from_states(ds, [False, True, True, False, True,
                                      False]) == [
            (date(2026, 1, 2), date(2026, 1, 4)),
            (date(2026, 1, 5), date(2026, 1, 6)),
        ]

    def test_open_end(self):
        ds = [date(2026, 1, d) for d in range(1, 4)]
        assert spans_from_states(ds, [False, True, True]) == [
            (date(2026, 1, 2), None)]

    def test_none(self):
        ds = [date(2026, 1, d) for d in range(1, 4)]
        assert spans_from_states(ds, [False] * 3) == []


class TestScan:
    def test_invariants(self):
        rows = asta_periods(2026)
        assert rows, "a year always has asta windows"
        for r in rows:
            assert r["asta"].year == 2026
            assert r["udaya"] is None or r["udaya"] > r["asta"]
            assert r["udaya"] is None or r["udaya"].year in (2026, 2027)
        for g in (Graha.VENUS, Graha.JUPITER):
            own = sorted(r["asta"] for r in rows if r["planet"] == g)
            assert own == sorted(set(own)), "no duplicate starts"
            assert len(own) >= 1, f"{g} goes combust yearly"

    def test_jupiter_2026_window(self):
        # Spot-check shape, not published-table dates: ~month-long.
        rows = [r for r in asta_periods(2026)
                if r["planet"] == Graha.JUPITER]
        assert len(rows) == 1
        span = (rows[0]["udaya"] - rows[0]["asta"]).days
        assert 20 <= span <= 45
