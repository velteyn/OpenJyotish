"""Tests for Bhava/Chalit methods (default Placidus/equal vs Sripati)."""

import pytest

from jhora.calc.chalit import ChalitComputer, sripati_bhavas
from jhora.charts.chart import ChartBuilder


def _jalkot():
    return ChartBuilder().build(2001, 2, 24, 6 + 11 / 60,
                                lat=18 + 38 / 60, lon=77 + 12 / 60,
                                tz="+0530", ayanamsa="lahiri")


def _chennai():
    return ChartBuilder().build(1970, 4, 4, 23.3, lat=13.08, lon=80.27,
                                tz="-5.5", ayanamsa="lahiri")


class TestSripatiSpans:
    def test_tile_360_and_anchors(self):
        for cd in (_jalkot(), _chennai()):
            spans = sripati_bhavas(cd.ascendant, cd.mc)
            assert len(spans) == 12
            begins = [b for b, _ in spans]
            total = sum((b2 - b1) % 360.0
                        for b1, b2 in zip(begins, begins[1:] + begins[:1]))
            assert total == pytest.approx(360.0)
            assert spans[0][1] == pytest.approx(cd.ascendant % 360.0)
            assert spans[9][1] == pytest.approx(cd.mc % 360.0)

    def test_matches_traditional_helper(self):
        from jhora.export.traditional import _sripati_bhavas
        for cd in (_jalkot(), _chennai()):
            assert sripati_bhavas(cd.ascendant, cd.mc) == \
                _sripati_bhavas(cd)


class TestSripatiMethod:
    def test_nine_entries_valid_houses(self):
        for cd in (_jalkot(), _chennai()):
            r = ChalitComputer(cd).compute(method="sripati")
            assert len(r.entries) == 9
            assert all(1 <= e.cusp_house <= 12 for e in r.entries)

    def test_bad_method_rejected(self):
        with pytest.raises(ValueError, match="bhava method"):
            ChalitComputer(_jalkot()).compute(method="bogus")

    def test_default_unchanged(self):
        for cd in (_jalkot(), _chennai()):
            a = ChalitComputer(cd).compute()
            b = ChalitComputer(cd).compute(method="default")
            assert [(e.graha, e.cusp_house) for e in a.entries] == \
                   [(e.graha, e.cusp_house) for e in b.entries]


class TestBhavaMethodCli:
    def test_sripati_flag(self):
        from typer.testing import CliRunner
        from jhora.cli.main import app
        r = CliRunner().invoke(app, [
            "chart", "2001-02-24 06:11:00 +0530 18.6333 77.2",
            "--chalit", "--bhava-method", "sripati"])
        assert r.exit_code == 0, r.output
        assert "Chalit" in r.output

    def test_bad_method(self):
        from typer.testing import CliRunner
        from jhora.cli.main import app
        r = CliRunner().invoke(app, [
            "chart", "2001-02-24 06:11:00 +0530 18.6333 77.2",
            "--chalit", "--bhava-method", "bogus"])
        assert r.exit_code == 2
