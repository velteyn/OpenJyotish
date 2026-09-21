"""Tests for Yoga/Nakshatra Pravesha charts + pravesha dasa engines.

Golden rules: tithi/karana/yoga index tables cross-checked against the
mirrored implementation; return-chart finders verified by angle
recurrence on the 1990 fixture.
"""

from jhora.calc.pravesha import (
    NakshatraPraveshaCalculator,
    YogaPraveshaCalculator,
    yoga_angle,
)
from jhora.charts.chart import ChartBuilder
from jhora.dasas.base import DasaOptions
from jhora.dasas.pravesha import (
    KaranaChaturaaseetiDasa,
    TithiAshtottariDasa,
    TithiYoginiDasa,
    YogaVimsottariDasa,
    karana_serial,
    tithi_index,
    yoga_index,
)
from jhora.types.dasa import PeriodLevel
from jhora.types.graha import Graha


def _chart():
    cd = ChartBuilder().build(
        year=1990, month=1, day=15, hour=17.5,
        lat=12.9716, lon=77.5946, tz="+0530")
    chart = {"planets": {g: {"longitude": p.longitude}
                         for g, p in cd.planets.items()}}
    return cd, chart


def _md_only():
    return DasaOptions(subdivision_level=PeriodLevel.MAHADASA,
                       include_subperiods=False)


def test_indices_match_reference_panchanga():
    # Independent clipboard: 1990-01-15 17:30 is Krishna Panchami.
    _, chart = _chart()
    assert tithi_index(chart) == 19  # 20th tithi, Krishna Panchami
    assert karana_serial(chart) == 39
    assert 1 <= yoga_index(chart) <= 27


def test_tithi_ashtottari_table():
    _, chart = _chart()
    mds = TithiAshtottariDasa(_md_only()).compute(0.0, chart)
    assert len(mds) == 8
    assert round(sum(m.duration_years for m in mds), 6) == 108.0
    # Tithi 20 → Jupiter 19y.
    assert mds[0].lord_name == "Jupiter"
    assert mds[0].duration_years == 19.0
    assert [m.lord_name for m in mds] == [
        "Jupiter", "Rahu", "Venus", "Sun",
        "Moon", "Mars", "Mercury", "Saturn"]
    assert all(abs(a.end_jd - b.start_jd) < 1e-6
               for a, b in zip(mds, mds[1:]))


def test_tithi_yogini_table():
    _, chart = _chart()
    mds = TithiYoginiDasa(_md_only()).compute(0.0, chart)
    assert len(mds) == 8
    assert round(sum(m.duration_years for m in mds), 6) == 36.0
    assert mds[0].lord_name == "Jupiter"
    assert mds[0].duration_years == 3.0


def test_karana_chaturaaseeti_table():
    _, chart = _chart()
    mds = KaranaChaturaaseetiDasa(_md_only()).compute(0.0, chart)
    assert len(mds) == 7
    assert [round(m.duration_years) for m in mds] == [12] * 7
    # Karana serial 39 → Mars.
    assert mds[0].lord_name == "Mars"
    assert all(abs(a.end_jd - b.start_jd) < 1e-6
               for a, b in zip(mds, mds[1:]))


def test_yoga_vimsottari_table():
    _, chart = _chart()
    mds = YogaVimsottariDasa(_md_only()).compute(0.0, chart)
    assert len(mds) == 9
    assert round(sum(m.duration_years for m in mds), 6) == 120.0
    # Yoga 5 → Sun 6y (standard Vimsottari years).
    assert mds[0].lord_name == "Sun"
    assert mds[0].duration_years == 6.0
    assert [m.lord_name for m in mds] == [
        "Sun", "Moon", "Mars", "Rahu", "Jupiter",
        "Mercury", "Saturn", "Ketu", "Venus"]


def test_yoga_pravesha_recurs_angle():
    cd, _ = _chart()
    entry = YogaPraveshaCalculator(cd).compute(2026)
    assert entry.chart is not None
    got = yoga_angle(
        entry.chart.planet(Graha.SUN).longitude,
        entry.chart.planet(Graha.MOON).longitude)
    assert min(abs(got - entry.target_angle),
               360 - abs(got - entry.target_angle)) < 0.5
    assert "2026-01" in entry.event_date  # annual, near birthday


def test_nakshatra_pravesha_recurs_moon():
    cd, _ = _chart()
    entry = NakshatraPraveshaCalculator(cd).compute(2026, 3)
    assert entry.chart is not None
    got = entry.chart.planet(Graha.MOON).longitude
    assert min(abs(got - entry.target_angle),
               360 - abs(got - entry.target_angle)) < 0.5
    assert entry.event_date.startswith("2026-03")


def test_cli_pravesha_commands_run():
    from typer.testing import CliRunner
    from jhora.cli.main import app
    out = CliRunner().invoke(
        app, ["yoga-pravesha", "1990-01-15 17:30:00 +0530 12.9716 77.5946",
              "--year", "2026"])
    assert out.exit_code == 0, out.output
    assert "Yoga Pravesha" in out.stdout
    out2 = CliRunner().invoke(
        app, ["nakshatra-pravesha",
              "1990-01-15 17:30:00 +0530 12.9716 77.5946",
              "--year", "2026", "--month", "3"])
    assert out2.exit_code == 0, out2.output
    assert "Nakshatra Pravesha" in out2.stdout


def test_cli_pravesha_dasas_run():
    from typer.testing import CliRunner
    from jhora.cli.main import app
    bd = "1990-01-15 17:30:00 +0530 12.9716 77.5946"
    for sys in ("tithi-ashtottari", "tithi-yogini",
                "karana-chaturaaseeti", "yoga-vimsottari"):
        out = CliRunner().invoke(app, ["dasa", bd, sys])
        assert out.exit_code == 0, (sys, out.output)
