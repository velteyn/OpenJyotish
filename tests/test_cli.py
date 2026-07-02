"""Tests for CLI main (parse_birthdata, varga/variant parsing, chart_to_dict)."""

import pytest
from typer import Exit

from jhora.cli.main import parse_birthdata, _chart_to_dict, _parse_varga_level, _parse_variant
from jhora.types.varga import VargaLevel, VargaVariant


class TestParseBirthdata:
    def test_standard_format(self):
        result = parse_birthdata("1970-04-04 17:48:20 +0530 13.08 80.27")
        assert result["year"] == 1970
        assert result["month"] == 4
        assert result["day"] == 4
        assert abs(result["hour"] - (17 + 48/60 + 20/3600)) < 0.001
        assert result["lat"] == 13.08
        assert result["lon"] == 80.27
        assert result["tz"] == "+0530"

    def test_noon_birth(self):
        result = parse_birthdata("2000-06-15 12:00:00 +0530 28.61 77.23")
        assert result["year"] == 2000
        assert abs(result["hour"] - 12.0) < 0.001

    def test_midnight_birth(self):
        result = parse_birthdata("1985-03-21 00:00:00 -0500 40.71 -74.01")
        assert abs(result["hour"] - 0.0) < 0.001
        assert result["tz"] == "-0500"
        assert result["lon"] == -74.01

    def test_no_seconds(self):
        result = parse_birthdata("1999-12-31 23:45 +0530 13.08 80.27")
        assert abs(result["hour"] - (23 + 45/60)) < 0.001

    def test_lat_lon_floats(self):
        result = parse_birthdata("2020-01-01 06:30:00 +0000 51.5074 -0.1278")
        assert result["lat"] == 51.5074
        assert result["lon"] == -0.1278


class TestParseVargaLevel:
    def test_d1_short_name(self):
        assert _parse_varga_level("D-1") == VargaLevel.D_1
        assert _parse_varga_level("d1") == VargaLevel.D_1

    def test_d9_levels(self):
        assert _parse_varga_level("D-9") == VargaLevel.D_9
        assert _parse_varga_level("d9") == VargaLevel.D_9

    def test_named_levels(self):
        assert _parse_varga_level("navamsa") == VargaLevel.D_9
        assert _parse_varga_level("navamsha") == VargaLevel.D_9
        assert _parse_varga_level("hora") == VargaLevel.D_2
        assert _parse_varga_level("drekkana") == VargaLevel.D_3
        assert _parse_varga_level("trimsamsa") == VargaLevel.D_30

    def test_various_levels(self):
        assert _parse_varga_level("D-2") == VargaLevel.D_2
        assert _parse_varga_level("D-3") == VargaLevel.D_3
        assert _parse_varga_level("D-7") == VargaLevel.D_7
        assert _parse_varga_level("D-10") == VargaLevel.D_10
        assert _parse_varga_level("D-12") == VargaLevel.D_12
        assert _parse_varga_level("D-16") == VargaLevel.D_16
        assert _parse_varga_level("D-20") == VargaLevel.D_20
        assert _parse_varga_level("D-27") == VargaLevel.D_27
        assert _parse_varga_level("D-60") == VargaLevel.D_60

    def test_invalid_level_exits(self):
        with pytest.raises(Exit):
            _parse_varga_level("D-999")

    def test_invalid_name_exits(self):
        with pytest.raises(Exit):
            _parse_varga_level("invalidvarga")


class TestParseVariant:
    def test_default(self):
        assert _parse_variant("default") == VargaVariant.DEFAULT

    def test_common_variants(self):
        assert _parse_variant("k") == VargaVariant.K
        assert _parse_variant("km") == VargaVariant.KM
        assert _parse_variant("ukm") == VargaVariant.UKM
        assert _parse_variant("rev") == VargaVariant.REV
        assert _parse_variant("trd") == VargaVariant.TRD

    def test_bhava_variants(self):
        assert _parse_variant("b") == VargaVariant.B
        assert _parse_variant("bhava") == VargaVariant.B

    def test_case_insensitive(self):
        assert _parse_variant("DEFAULT") == VargaVariant.DEFAULT
        assert _parse_variant("K") == VargaVariant.K

    def test_knrao(self):
        assert _parse_variant("knrao") == VargaVariant.K_N_RAO

    def test_invalid_variant_exits(self):
        with pytest.raises(Exit):
            _parse_variant("nonexistent")


class TestChartToDict:
    def test_returns_dict_with_keys(self, ref_chart):
        result = _chart_to_dict(ref_chart)
        assert "planets" in result
        assert "lagna_lon" in result

    def test_all_planets_present(self, ref_chart):
        result = _chart_to_dict(ref_chart)
        assert len(result["planets"]) == 9

    def test_longitude_present(self, ref_chart):
        result = _chart_to_dict(ref_chart)
        for g, d in result["planets"].items():
            assert "longitude" in d
            assert "speed" in d
            assert 0.0 <= d["longitude"] < 360.0

    def test_lagna_lon_matches(self, ref_chart):
        result = _chart_to_dict(ref_chart)
        assert result["lagna_lon"] == ref_chart.ascendant