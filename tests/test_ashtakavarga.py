"""Tests for Ashtakavarga — eight-sourced strength computation."""
import pytest
from jhora.calc.ashtakavarga import (
    bhinna_ashtakavarga,
    all_bhinna_ashtakavarga,
    sarva_ashtakavarga,
    prastara_ashtakavarga,
    trikona_shodhana,
    trikona_shodhana_all,
    ekadhipatya_shodhana,
    sodhya_pinda,
    kakshya_bindu_table,
    all_kakshya_tables,
    kakshya_totals,
    kakshya_index_from_degree,
    _OCCUPANT_GRAHAS,
    _BAV_MATRIX,
    _BAV_TOTALS,
)
from jhora.charts.chart import ChartBuilder
from jhora.types.graha import Graha


@pytest.fixture(scope="module")
def chart():
    """Chart used in all ashtakavarga tests."""
    builder = ChartBuilder()
    utc_hour = 12.0
    local_hour = utc_hour + 5.5  # IST (17:30)
    return builder.build(1990, 1, 15, local_hour, 12.9716, 77.5946, tz="-5.5")


@pytest.fixture(scope="module")
def ref_chart():
    """Reference birth chart (1970-04-04 17:48:20 UT = 23:18:20 IST, Chennai)."""
    builder = ChartBuilder()
    utc_hour = 17 + 48 / 60 + 20 / 3600
    local_hour = utc_hour + 5.5  # IST
    return builder.build(
        year=1970, month=4, day=4,
        hour=local_hour,
        lat=13.08, lon=80.27,
        tz="-5.5", ayanamsa="lahiri",
    )


class TestMatrix:
    """The (subject, contributor) benefic matrix: 7 subjects × 8 contributors."""

    def test_all_subjects_have_all_contributors(self):
        for g in _OCCUPANT_GRAHAS:
            assert g in _BAV_MATRIX
            row = _BAV_MATRIX[g]
            for c in _OCCUPANT_GRAHAS:
                assert c in row
            assert "LAGNA" in row

    def test_row_sums_are_fixed_totals(self):
        """Each subject's matrix rows sum to its canonical BAV total."""
        for g in _OCCUPANT_GRAHAS:
            total = sum(len(houses) for houses in _BAV_MATRIX[g].values())
            assert total == _BAV_TOTALS[g], f"{g.name}: {total}"

    def test_expected_totals(self):
        assert _BAV_TOTALS == {
            Graha.SUN: 48, Graha.MOON: 49, Graha.MARS: 39,
            Graha.MERCURY: 54, Graha.JUPITER: 56, Graha.VENUS: 52,
            Graha.SATURN: 39,
        }


class TestBAV:
    """Bhinna Ashtakavarga tests."""

    def test_bav_output_type(self, chart):
        bav = bhinna_ashtakavarga(chart, Graha.SUN)
        assert isinstance(bav, list)
        assert len(bav) == 12

    def test_bav_sums_positive(self, chart):
        for g in _OCCUPANT_GRAHAS:
            bav = bhinna_ashtakavarga(chart, g)
            assert all(b >= 0 for b in bav)
            assert sum(bav) > 0

    def test_bav_max_per_house(self, chart):
        """No house should exceed 8 (max bindus from 8 references)."""
        for g in _OCCUPANT_GRAHAS:
            bav = bhinna_ashtakavarga(chart, g)
            assert all(b <= 8 for b in bav)

    def test_bav_different_per_planet(self, chart):
        """BAVs must differ between planets (otherwise algorithm is wrong)."""
        bavs = all_bhinna_ashtakavarga(chart)
        sun = bavs[Graha.SUN]
        moon = bavs[Graha.MOON]
        assert sun != moon, "BAV(Sun) and BAV(Moon) must differ"

    def test_all_bavs_returned(self, chart):
        bavs = all_bhinna_ashtakavarga(chart)
        for g in _OCCUPANT_GRAHAS:
            assert g in bavs
            assert len(bavs[g]) == 12

    def test_bav_fixed_totals(self, chart):
        """Each BAV sums to its canonical total in every chart."""
        bavs = all_bhinna_ashtakavarga(chart)
        for g in _OCCUPANT_GRAHAS:
            assert sum(bavs[g]) == _BAV_TOTALS[g], f"{g.name}"

    def test_bav_totals_invariant_across_charts(self, chart, ref_chart):
        """Distribution moves, totals don't."""
        for cd in (chart, ref_chart):
            bavs = all_bhinna_ashtakavarga(cd)
            for g in _OCCUPANT_GRAHAS:
                assert sum(bavs[g]) == _BAV_TOTALS[g]


class TestSAV:
    """Sarva Ashtakavarga tests."""

    def test_sav_output(self, chart):
        sav = sarva_ashtakavarga(chart)
        assert isinstance(sav, list)
        assert len(sav) == 12

    def test_sav_is_sum_of_bavs(self, chart):
        sav = sarva_ashtakavarga(chart)
        bavs = all_bhinna_ashtakavarga(chart)
        for h in range(12):
            expected = sum(bavs[g][h] for g in _OCCUPANT_GRAHAS)
            assert sav[h] == expected

    def test_sav_max_per_house(self, chart):
        """SAV max per house = sum of 7 BAVs each ≤ 8 → ≤ 56."""
        sav = sarva_ashtakavarga(chart)
        assert all(s <= 56 for s in sav)

    def test_sav_total_is_337(self, chart, ref_chart):
        """Sarvashtakavarga sums to 337 in every chart."""
        for cd in (chart, ref_chart):
            assert sum(sarva_ashtakavarga(cd)) == 337

    def test_sav_no_zero_houses(self, chart):
        """Every rasi receives bindus (the zero-house bug is gone)."""
        assert all(s > 0 for s in sarva_ashtakavarga(chart))

    def test_validated_distribution(self):
        """Spot-check against an independent implementation (jyotishganit).

        1973-03-13 13:55 +0100 Padua: SAV matched house-for-house.
        """
        cd = ChartBuilder().build(1973, 3, 13, 13 + 55 / 60,
                                  lat=45.4130, lon=11.8806, tz="+0100")
        assert sarva_ashtakavarga(cd) == [30, 25, 25, 31, 27, 29,
                                          33, 32, 40, 22, 20, 23]


class TestPAV:
    """Prastara Ashtakavarga tests (per-subject contributor rows)."""

    def test_pav_output(self, chart):
        pav = prastara_ashtakavarga(chart, Graha.SUN)
        assert isinstance(pav, dict)
        assert len(pav) == 8  # 7 planets + Lagna

    def test_pav_values_01(self, chart):
        """Each PAV cell is binary (0 or 1) — one contributor, one house."""
        pav = prastara_ashtakavarga(chart, Graha.MARS)
        for ref_name, row in pav.items():
            for h in range(12):
                assert row[h] in (0, 1), f"{ref_name}[{h}]={row[h]}"

    def test_pav_columns_equal_bav(self, chart):
        """Column sums of the prastara equal the subject's BAV."""
        for g in _OCCUPANT_GRAHAS:
            pav = prastara_ashtakavarga(chart, g)
            bav = bhinna_ashtakavarga(chart, g)
            for h in range(12):
                assert sum(row[h] for row in pav.values()) == bav[h]


class TestTrikonaShodhana:
    """Trikona Shodhana (triangular reduction) tests."""

    def test_reduces_bindus(self):
        bav = [5, 3, 4, 2, 6, 1, 3, 4, 2, 5, 0, 3]
        reduced = trikona_shodhana(bav)
        assert all(r <= b for r, b in zip(reduced, bav))

    def test_groups_have_zero(self):
        """After trikona shodhana, at least one house in each trinal group
        should be 0."""
        bav = [3, 2, 4, 1, 5, 3, 2, 4, 1, 3, 2, 4]
        reduced = trikona_shodhana(bav)
        groups = [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]
        for a, b, c in groups:
            assert reduced[a] == 0 or reduced[b] == 0 or reduced[c] == 0

    def test_subtracts_minimum_from_all_three(self):
        """The minimum is subtracted from every group member — including
        the third (regression: it used to be zeroed unconditionally)."""
        bav = [0] * 12
        bav[0], bav[4], bav[8] = 5, 2, 4
        reduced = trikona_shodhana(bav)
        assert (reduced[0], reduced[4], reduced[8]) == (3, 0, 2)


class TestEkadhipatyaShodhana:
    """Ekadhipatya Shodhana (lordship reduction) tests."""

    def test_sun_moon_unchanged(self):
        """Sun and Moon own only one sign — their BAVs should pass through."""
        bavs = {
            Graha.SUN: [5, 3, 4, 2, 6, 1, 3, 4, 2, 5, 0, 3],
            Graha.MOON: [4, 2, 3, 1, 5, 2, 4, 3, 1, 4, 1, 2],
            Graha.MARS: [3, 4, 2, 3, 4, 2, 5, 3, 2, 3, 2, 4],
            Graha.MERCURY: [2, 5, 1, 4, 3, 1, 2, 4, 3, 2, 3, 5],
            Graha.JUPITER: [4, 3, 5, 2, 4, 3, 1, 5, 2, 4, 3, 2],
            Graha.VENUS: [3, 2, 4, 1, 3, 2, 5, 4, 1, 3, 2, 4],
            Graha.SATURN: [2, 4, 3, 5, 2, 4, 3, 1, 4, 2, 3, 1],
        }
        result = ekadhipatya_shodhana(bavs)
        assert result[Graha.SUN] == bavs[Graha.SUN]
        assert result[Graha.MOON] == bavs[Graha.MOON]

    def test_dual_lordship_reduction_logic(self):
        """Mars owns Aries(0) and Scorpio(7). If bindus are 5 and 2,
        the higher reduces to difference 3, lower stays 2."""
        bavs = {
            Graha.SUN: [5, 3, 4, 2, 6, 1, 3, 4, 2, 5, 0, 3],
            Graha.MOON: [4, 2, 3, 1, 5, 2, 4, 3, 1, 4, 1, 2],
            Graha.MARS: [5, 4, 2, 3, 4, 2, 5, 2, 2, 3, 2, 4],
            Graha.MERCURY: [2, 5, 1, 4, 3, 1, 2, 4, 3, 2, 3, 5],
            Graha.JUPITER: [4, 3, 5, 2, 4, 3, 1, 5, 2, 4, 3, 2],
            Graha.VENUS: [3, 2, 4, 1, 3, 2, 5, 4, 1, 3, 2, 4],
            Graha.SATURN: [2, 4, 3, 5, 2, 4, 3, 1, 4, 2, 3, 1],
        }
        result = ekadhipatya_shodhana(bavs)
        mars_orig = bavs[Graha.MARS]
        mars_new = result[Graha.MARS]
        # Mars owns Aries(0) and Scorpio(7): orig [5, 2] → diff 3
        assert mars_new[0] == 3  # 5 - 2 = 3
        assert mars_new[7] == 2  # lower stays


class TestSodhyaPinda:
    """Sodhya Pinda (Yoga Pinda) tests."""

    def test_return_type(self, chart):
        sp = sodhya_pinda(chart)
        assert isinstance(sp, dict)
        assert len(sp) == 7

    def test_all_positive(self, chart):
        sp = sodhya_pinda(chart)
        for g in _OCCUPANT_GRAHAS:
            assert sp[g] >= 0

    def test_sun_moon_sodhya(self, ref_chart):
        """Smoke: compute sodhya pinda for reference chart."""
        sp = sodhya_pinda(ref_chart)
        # Sun and Moon should have pinda values (positive).
        assert sp[Graha.SUN] >= 0
        assert sp[Graha.MOON] >= 0


class TestEdgeCases:
    """Edge case tests for Ashtakavarga."""

    def test_varahamihira_variant_not_implemented(self, chart):
        """The Varahamihira variant has no validated matrix — it must fail
        loudly, never silently produce numbers."""
        with pytest.raises(NotImplementedError):
            bhinna_ashtakavarga(chart, Graha.MOON, parasara_moon=False)
        with pytest.raises(NotImplementedError):
            bhinna_ashtakavarga(chart, Graha.VENUS, parasara_venus=False)
        with pytest.raises(NotImplementedError):
            sarva_ashtakavarga(chart, parasara_moon=False)


class TestKakshya:
    """Kakshya-level bindu tests."""

    def test_kakshya_index_from_degree(self):
        assert kakshya_index_from_degree(0.0) == 0
        assert kakshya_index_from_degree(3.74) == 0
        assert kakshya_index_from_degree(3.75) == 1
        assert kakshya_index_from_degree(7.5) == 2
        assert kakshya_index_from_degree(15.0) == 4  # Jupiter
        assert kakshya_index_from_degree(29.99) == 7  # Lagna
        assert kakshya_index_from_degree(30.0) == 7  # clamp

    def test_kakshya_table_shape(self, chart):
        for g in _OCCUPANT_GRAHAS:
            table = kakshya_bindu_table(g, chart)
            assert len(table) == 12
            for h in range(12):
                assert len(table[h]) == 8

    def test_kakshya_values_binary(self, chart):
        for g in _OCCUPANT_GRAHAS:
            table = kakshya_bindu_table(g, chart)
            for h in range(12):
                for k in range(8):
                    assert table[h][k] in (0, 1), f"{g.name}[{h}][{k}]={table[h][k]}"

    def test_kakshya_sum_equals_bav(self, chart):
        """Sum of all 8 kakshyas in a house should equal that house's BAV."""
        for g in _OCCUPANT_GRAHAS:
            bav = bhinna_ashtakavarga(chart, g)
            table = kakshya_bindu_table(g, chart)
            for h in range(12):
                assert sum(table[h]) == bav[h], (
                    f"{g.name} house {h}: kakshya sum {sum(table[h])} vs BAV {bav[h]}"
                )

    def test_all_kakshya_tables(self, chart):
        all_tables = all_kakshya_tables(chart)
        assert len(all_tables) == 7
        for g in _OCCUPANT_GRAHAS:
            assert g in all_tables

    def test_kakshya_totals_shape(self, ref_chart):
        totals = kakshya_totals(ref_chart)
        assert len(totals) == 8  # 7 grahas + Lagna
        for ref_name, houses in totals.items():
            assert len(houses) == 12

    def test_kakshya_matches_prastara(self, ref_chart):
        """Kakshya columns and prastara rows are two views of the same
        contributor math: table[H][K] == prastara_row(K-lord)[H]."""
        from jhora.calc.ashtakavarga import (prastara_ashtakavarga,
                                             _KAKSHYA_REFERENCES, ref_to_str)
        for g in _OCCUPANT_GRAHAS:
            table = kakshya_bindu_table(g, ref_chart)
            pav = prastara_ashtakavarga(ref_chart, g)
            for h in range(12):
                for k, ref in enumerate(_KAKSHYA_REFERENCES):
                    assert table[h][k] == pav[ref_to_str(ref)][h]
