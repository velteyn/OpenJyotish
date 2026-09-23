"""Tests for the dasa entry chart (period opening-moment chart)."""

import pytest
from typer.testing import CliRunner

from jhora.calc.dasa_entry import (dasa_entry, find_period, format_dasa_entry,
                                   parse_path)
from jhora.charts.chart import ChartBuilder
from jhora.cli.main import app
from jhora.dasas.vimsottari import VimsottariDasa

runner = CliRunner()
JALKOT = "2001-02-24 06:11:00 +0530 18.6333 77.2"


def _jalkot():
    return ChartBuilder().build(2001, 2, 24, 6 + 11 / 60,
                                lat=18 + 38 / 60, lon=77 + 12 / 60,
                                tz="+0530", ayanamsa="lahiri")


def _periods(cd):
    eng = VimsottariDasa()
    chart = {"planets": {g.value: {"longitude": p.longitude}
                         for g, p in cd.planets.items()},
             "lagna_lon": cd.ascendant}
    return eng.compute(cd.julian_day, chart)


class TestFindPeriod:
    def test_md_ad_path(self):
        periods = _periods(_jalkot())
        p = find_period(periods, ["Rahu", "Saturn"])
        assert p is not None and p.lord_name == "Saturn"

    def test_case_insensitive_prefix(self):
        periods = _periods(_jalkot())
        assert find_period(periods, ["rah", "sat"]).lord_name == "Saturn"

    def test_no_match(self):
        periods = _periods(_jalkot())
        assert find_period(periods, ["Rahu", "Pluto"]) is None
        assert find_period(periods, ["S"]) is None  # ambiguous: Saturn/Sun

    def test_parse_path(self):
        assert parse_path("Jupiter/Saturn") == ["Jupiter", "Saturn"]
        assert parse_path(" Jupiter > Saturn ") == ["Jupiter", "Saturn"]


class TestEntryChart:
    def test_rahu_saturn_opens_2001_06_30(self):
        # Regression pin (UT date of the AD opening).
        import swisseph as swe
        period, _ = dasa_entry(_jalkot(), ["Rahu", "Saturn"])
        y, m, d, _h = swe.revjul(period.start_jd)
        assert (int(y), int(m), int(d)) == (2001, 6, 30)

    def test_entry_moment_matches_period_start(self):
        cd = _jalkot()
        period, entry = dasa_entry(cd, ["Rahu", "Saturn"])
        assert abs(entry.julian_day - period.start_jd) < 2e-4  # ~20 s
        assert entry.latitude == pytest.approx(cd.latitude)
        assert entry.longitude == pytest.approx(cd.longitude)

    def test_entry_at_birth_matches_natal(self):
        cd = _jalkot()
        period, entry = dasa_entry(cd, ["Rahu", "Rahu"])
        assert abs(entry.ascendant - cd.ascendant) < 1e-3
        from jhora.types.graha import Graha
        assert abs(entry.planet(Graha.MOON).longitude -
                   cd.planet(Graha.MOON).longitude) < 1e-3

    def test_bad_path_raises(self):
        with pytest.raises(ValueError, match="expected one of"):
            dasa_entry(_jalkot(), ["Rahu", "Pluto"])

    def test_format_mentions_lords(self):
        cd = _jalkot()
        period, entry = dasa_entry(cd, ["Rahu", "Saturn"])
        text = format_dasa_entry(["Rahu", "Saturn"], period, cd, entry)
        assert "Rahu/Saturn" in text
        assert "Entry lagna" in text
        assert "Saturn" in text


class TestDasaEntryCli:
    def test_dasa_entry_command(self):
        result = runner.invoke(app, ["dasa-entry", JALKOT, "Rahu/Saturn"])
        assert result.exit_code == 0, result.output
        assert "Rahu/Saturn" in result.output
        assert "Entry lagna" in result.output

    def test_dasa_entry_bad_path(self):
        result = runner.invoke(app, ["dasa-entry", JALKOT, "Rahu/Pluto"])
        assert result.exit_code == 1
