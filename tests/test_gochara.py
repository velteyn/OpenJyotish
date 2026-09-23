"""Tests for Gochara (Transit) analysis."""
import pytest
from jhora.calc.gochara import (
    GOCHARA_GOOD,
    GOCHARA_VEDHA,
    TransitEntry,
    TransitResult,
    compute_transits,
    vedha_house,
)
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


class TestGocharaVedha:
    """Vedha (obstruction) pairs — Phaladeepika ch. 26."""

    def test_tables_are_consistent(self):
        for g, good in GOCHARA_GOOD.items():
            assert set(GOCHARA_VEDHA[g]) == set(good)
            assert all(1 <= v <= 12 for v in GOCHARA_VEDHA[g].values())

    def test_vedha_house_is_not_a_good_house(self):
        # The vedha house is a distinct obstruction point, not itself a
        # favourable house (Raman, Hindu Predictive Astrology ch. 34).
        for g, pairs in GOCHARA_VEDHA.items():
            for h, v in pairs.items():
                assert v != h

    def test_vedha_house_lookup(self):
        assert vedha_house(Graha.SUN, 3) == 9
        assert vedha_house(Graha.SUN, 6) == 12
        assert vedha_house(Graha.SATURN, 11) == 5
        assert vedha_house(Graha.SUN, 1) == 0  # not a good house

    def test_nodes_have_no_vedha(self):
        assert vedha_house(Graha.RAHU, 3) == 0
        assert vedha_house(Graha.KETU, 3) == 0

    def test_vedha_requires_a_favourable_house(self, chart):
        result = compute_transits(chart)
        for e in result.entries:
            if e.is_vedha:
                assert e.is_good_transit
                assert e.vedha_house

    def test_vedha_house_only_set_for_good_houses(self, chart):
        result = compute_transits(chart)
        for e in result.entries:
            if not e.is_good_transit:
                assert e.vedha_house == 0
                assert not e.is_vedha

    def test_good_flag_matches_table(self, chart):
        result = compute_transits(chart)
        for e in result.entries:
            assert e.is_good_transit == (
                e.house_from_moon in GOCHARA_GOOD.get(e.graha, ()))


class TestSwissEphemerisIdMapping:
    """Regression: SE IDs must map to the right graha.

    The SE order is Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn; using
    the Vedic order instead swapped Mercury/Mars and Venus/Jupiter.
    """

    def test_transits_at_birth_match_natal(self, chart):
        result = compute_transits(chart, transit_jd=chart.julian_day)
        for e in result.entries:
            natal = chart.planets[e.graha]
            assert e.transit_rasi_name == natal.rasi.short_name, e.graha
            lon = e.transit_rasi * 30 + e.transit_degrees
            assert abs(lon - natal.longitude) < 0.01

    def test_mapping_is_se_order(self):
        from jhora.calc.gochara import _SE_TO_GRAHA
        assert _SE_TO_GRAHA == {
            0: Graha.SUN, 1: Graha.MOON, 2: Graha.MERCURY, 3: Graha.VENUS,
            4: Graha.MARS, 5: Graha.JUPITER, 6: Graha.SATURN,
        }
