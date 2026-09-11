"""Tests for Sphuta computation (Prasna Marga Ch V) and CLI surface."""

import pytest
from typer.testing import CliRunner

from jhora.cli.main import app
from jhora.calc import sphuta as S

runner = CliRunner()
JALKOT = "2001-02-24 06:11:00 +0530 18.6333 77.2"

# Worked JHora-lineage example (swisseph list): Jalkot 2001-02-24 06:11 +0530.
EXPECTED = {
    "Trisphuta": 117.794,
    "Chatusphuta": 69.414,
    "Panchasphuta": 148.385,
    "Mrityu": 37.592,
    "Beeja": 341.136,
    "Kshetra": 218.773,
    "Yoga": 270.728,
}


def _jalkot_inputs():
    from jhora.charts.chart import ChartBuilder
    from jhora.calc.muhurta import _sunrise_sunset
    from jhora.calc.upagraha import compute_temporal_upagrahas
    from jhora.types.graha import Graha
    import datetime
    cd = ChartBuilder().build(2001, 2, 24, 6 + 11 / 60,
                              lat=18 + 38 / 60, lon=77 + 12 / 60,
                              tz="+0530")
    day = datetime.datetime(2001, 2, 24)
    sr, ss = _sunrise_sunset(day, 18 + 38 / 60, 77 + 12 / 60, 5.5)
    gulika = next(r.longitude for r in
                  compute_temporal_upagrahas(cd, sr, ss)
                  if r.name == "Gulika")
    lon = lambda g: cd.planet(g).longitude  # noqa: E731
    return {
        "lagna": cd.ascendant, "sun": lon(Graha.SUN),
        "moon": lon(Graha.MOON), "mars": lon(Graha.MARS),
        "jupiter": lon(Graha.JUPITER), "venus": lon(Graha.VENUS),
        "rahu": lon(Graha.RAHU), "gulika": gulika,
    }


class TestStructuralIdentities:
    def test_direct_values(self):
        assert S.trisphuta(10.0, 20.0, 30.0) == pytest.approx(60.0)
        assert S.chatusphuta(100.0, 311.0) == pytest.approx(51.0)
        assert S.panchasphuta(70.0, 79.0) == pytest.approx(149.0)
        assert S.prana_sphuta(300.0, 218.0) == pytest.approx(
            (1500.0 + 218.0) % 360.0)
        assert S.deha_sphuta(319.0, 218.0) == pytest.approx(
            (2552.0 + 218.0) % 360.0)
        assert S.mrityu_sphuta(218.0, 311.0) == pytest.approx(
            (1526.0 + 311.0) % 360.0)
        assert S.beeja_sphuta(38.0, 350.0, 311.0) == pytest.approx(339.0)
        assert S.kshetra_sphuta(38.0, 319.0, 220.0) == pytest.approx(217.0)
        assert S.yoga_sphuta(311.0, 319.0) == pytest.approx(270.0)

    def test_bundle_chaining(self):
        out = S.compute_sphutas(lagna=300.0, sun=311.0, moon=319.0,
                                mars=220.0, jupiter=38.0, venus=350.0,
                                rahu=79.0, gulika=218.0)
        assert out["Chatusphuta"] == pytest.approx(
            (out["Trisphuta"] + 311.0) % 360.0)
        assert out["Panchasphuta"] == pytest.approx(
            (out["Chatusphuta"] + 79.0) % 360.0)
        assert set(out) == {"Trisphuta", "Chatusphuta", "Panchasphuta",
                            "Prana", "Deha", "Mrityu", "Beeja", "Kshetra",
                            "Yoga"}


class TestWorkedExample:
    def test_planet_only_sphutas(self):
        inp = _jalkot_inputs()
        got = S.compute_sphutas(**inp)
        for name in ("Beeja", "Kshetra", "Yoga"):
            delta = abs((got[name] - EXPECTED[name] + 180.0) % 360.0 - 180.0)
            assert delta < 0.1, f"{name}: {delta:.4f}"

    def test_gulika_derived_sphutas(self):
        inp = _jalkot_inputs()
        got = S.compute_sphutas(**inp)
        for name in ("Trisphuta", "Chatusphuta", "Panchasphuta"):
            delta = abs((got[name] - EXPECTED[name] + 180.0) % 360.0 - 180.0)
            assert delta < 1.5, f"{name}: {delta:.4f}"

    def test_mrityu_structure_and_reference(self):
        inp = _jalkot_inputs()
        got = S.compute_sphutas(**inp)
        assert got["Mrityu"] == pytest.approx(
            S.mrityu_sphuta(inp["gulika"], inp["sun"]))
        delta = abs((got["Mrityu"] - EXPECTED["Mrityu"] + 180.0) % 360.0
                    - 180.0)
        assert delta < 7.0, f"Mrityu: {delta:.4f}"


class TestSphutasCli:
    def test_sphutas_command(self):
        result = runner.invoke(app, ["sphutas", JALKOT])
        assert result.exit_code == 0, result.output
        for name in ("Trisphuta", "Chatusphuta", "Panchasphuta", "Prana",
                     "Deha", "Mrityu", "Beeja", "Kshetra", "Yoga"):
            assert name in result.output
