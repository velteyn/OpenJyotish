"""Tests for Gochara (Transit) analysis."""
import pytest
from jhora.calc.gochara import compute_transits, TransitEntry, TransitResult
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha


@pytest.fixture(scope="module")
def chart():
    builder = ChartBuilder()
    return builder.build(1990, 1, 15, 12.0, 12.9716, 77.5946, tz="Asia/Kolkata")


class TestGochara:
    def test_result_shape(self, chart):
        result = compute_transits(chart)
        assert isinstance(result, TransitResult)
        assert len(result.entries) == 7  # 7 planets
        assert len(result.sav) == 12

    def test_entries_are_transitentry(self, chart):
        result = compute_transits(chart)
        for e in result.entries:
            assert isinstance(e, TransitEntry)

    def test_all_planets_present(self, chart):
        result = compute_transits(chart)
        grahas = {e.graha for e in result.entries}
        expected = {Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                    Graha.JUPITER, Graha.VENUS, Graha.SATURN}
        assert grahas == expected

    def test_rasi_index_valid(self, chart):
        result = compute_transits(chart)
        for e in result.entries:
            assert 0 <= e.transit_rasi < 12

    def test_house_from_lagna_valid(self, chart):
        result = compute_transits(chart)
        for e in result.entries:
            assert 1 <= e.house_from_lagna <= 12
            assert 1 <= e.house_from_moon <= 12

    def test_bav_scores_nonnegative(self, chart):
        result = compute_transits(chart)
        for e in result.entries:
            assert e.bav_score >= 0
            assert e.sav_score >= 0

    def test_sav_length(self, chart):
        result = compute_transits(chart)
        assert len(result.sav) == 12

    def test_natal_info(self, chart):
        result = compute_transits(chart)
        assert result.natal_rasi == chart.lagna.rasi.value
        assert result.moon_rasi == chart.planets[Graha.MOON].rasi.value

    def test_is_favorable_boolean(self, chart):
        result = compute_transits(chart)
        for e in result.entries:
            assert isinstance(e.is_favorable, bool)

    def test_timestamp_present(self, chart):
        result = compute_transits(chart)
        assert result.timestamp is not None
